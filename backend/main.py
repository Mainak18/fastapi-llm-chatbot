from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from groq import Groq
from dotenv import load_dotenv
import os
import logging
import re

from database import get_db, init_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_TOKEN = os.getenv("API_TOKEN")

client = Groq(api_key=GROQ_API_KEY)
app = FastAPI(title="LLM Chatbot API")

# CORS so React frontend can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    logger.info("Database initialized")

class QueryRequest(BaseModel):
    query: str

def verify_token(authorization: str = Header(None)):
    if not authorization or authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return True

def is_safe_sql(sql: str) -> bool:
    """Only allow SELECT queries - block anything dangerous."""
    sql_lower = sql.lower().strip()
    if not sql_lower.startswith("select"):
        return False
    forbidden = ["drop", "delete", "update", "insert", "alter", "truncate", "create", ";--"]
    for word in forbidden:
        if word in sql_lower:
            return False
    return True

def clean_sql(sql: str) -> str:
    """Remove markdown code fences if LLM added them."""
    sql = re.sub(r"```sql\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```", "", sql)
    return sql.strip().rstrip(";")

@app.get("/")
def root():
    return {"message": "LLM Chatbot API is running!"}

@app.post("/query")
def process_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_token)
):
    user_query = request.query
    logger.info(f"Incoming query: {user_query}")

    prompt = f"""You are a SQL query generator. Convert the user's natural language 
question into a PostgreSQL SELECT query.

Table schema:
customers (customer_id INTEGER PRIMARY KEY, name TEXT, gender TEXT, location TEXT)

Rules:
- Return ONLY the SQL query, no explanation, no markdown.
- Only SELECT queries are allowed.
- Use case-insensitive matching with ILIKE for text comparisons.

User question: {user_query}

SQL query:"""

    try:
        # Call Groq LLM
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        sql_query = response.choices[0].message.content.strip()
        sql_query = clean_sql(sql_query)
        logger.info(f"Generated SQL: {sql_query}")

        # Safety check
        if not is_safe_sql(sql_query):
            raise HTTPException(status_code=400, detail=f"Unsafe SQL rejected: {sql_query}")

        # Execute
        result = db.execute(text(sql_query))
        rows = [dict(row._mapping) for row in result]
        logger.info(f"Query returned {len(rows)} rows")

        return {
            "user_query": user_query,
            "generated_sql": sql_query,
            "results": rows,
            "count": len(rows)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
