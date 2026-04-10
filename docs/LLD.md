# 📙 Low-Level Design (LLD)
## LLM-Powered Chatbot with FastAPI & PostgreSQL

**Project:** FastAPI + LLM Chatbot Challenge  
**Author:** Mainak Bhattacharjee  
**Version:** 1.0  
**Date:** April 2026

---

## 1. Introduction

This document provides implementation-level details of the chatbot system. It covers class structures, function signatures, database models, API contracts, and step-by-step execution flows. Read the [HLD](./HLD.md) first for the big picture.

---

## 2. Module Structure

```mermaid
graph TB
    subgraph "backend/"
        M[main.py<br/>FastAPI App]
        DB[database.py<br/>ORM Models]
        S[seed.py<br/>Sample Data]
        E[.env<br/>Config]
        R[requirements.txt]
    end

    M -->|imports| DB
    S -->|imports| DB
    M -->|reads| E

    subgraph "frontend/src/"
        A[App.js<br/>Main Component]
        C[App.css<br/>Styles]
    end

    A -->|imports| C

    M -.HTTP.-> A

    style M fill:#66bb6a,color:#fff
    style DB fill:#26a69a,color:#fff
    style S fill:#ffa726,color:#000
    style A fill:#42a5f5,color:#fff
    style C fill:#42a5f5,color:#fff
```

---

## 3. Database Layer (`database.py`)

### 3.1 Class Diagram

```mermaid
classDiagram
    class Base {
        <<SQLAlchemy DeclarativeBase>>
    }

    class Customer {
        +Integer customer_id PK
        +String name
        +String gender
        +String location
        +__tablename__ : "customers"
    }

    class SessionLocal {
        <<sessionmaker>>
        +autocommit: False
        +autoflush: False
        +bind: engine
    }

    class Engine {
        <<SQLAlchemy Engine>>
        +url: DATABASE_URL
    }

    Base <|-- Customer
    SessionLocal --> Engine
    Customer --> Base : inherits

    class Functions {
        <<module-level>>
        +get_db() Generator~Session~
        +init_db() None
    }
```

### 3.2 Responsibilities

| Component       | Responsibility                                         |
| --------------- | ------------------------------------------------------ |
| `Base`          | SQLAlchemy declarative base class                      |
| `Customer`      | ORM model for `customers` table                        |
| `engine`        | Database connection pool                               |
| `SessionLocal`  | Session factory                                        |
| `get_db()`      | FastAPI dependency for per-request DB sessions         |
| `init_db()`     | Creates tables if they don't exist                     |

### 3.3 Key Code

```python
class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    location = Column(String, nullable=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 4. API Layer (`main.py`)

### 4.1 Component Interaction

```mermaid
graph TB
    REQ[Incoming Request] --> MW[CORS Middleware]
    MW --> R[Route Handler<br/>/query]
    R --> AUTH[verify_token<br/>Dependency]
    AUTH -->|401 if invalid| ERR1[HTTPException]
    AUTH -->|Valid| DB_DEP[get_db<br/>Dependency]
    DB_DEP --> PB[Prompt Builder]
    PB --> GROQ[Groq Client]
    GROQ --> CL[clean_sql]
    CL --> VAL[is_safe_sql]
    VAL -->|False| ERR2[HTTPException 400]
    VAL -->|True| EXEC[db.execute]
    EXEC --> FMT[Format rows as dict]
    FMT --> RESP[JSON Response]

    style REQ fill:#f9a825,color:#000
    style AUTH fill:#ef5350,color:#fff
    style VAL fill:#ef5350,color:#fff
    style GROQ fill:#ab47bc,color:#fff
    style EXEC fill:#26a69a,color:#fff
    style RESP fill:#66bb6a,color:#fff
    style ERR1 fill:#d32f2f,color:#fff
    style ERR2 fill:#d32f2f,color:#fff
```

### 4.2 Function Specifications

#### `verify_token(authorization: str) -> bool`

| Attribute    | Value                                               |
| ------------ | --------------------------------------------------- |
| **Purpose**  | Check Bearer token in Authorization header          |
| **Input**    | `authorization: str` (from `Header(None)`)          |
| **Output**   | `True` if valid                                     |
| **Raises**   | `HTTPException(401)` if missing or invalid          |

#### `is_safe_sql(sql: str) -> bool`

| Attribute    | Value                                               |
| ------------ | --------------------------------------------------- |
| **Purpose**  | Whitelist SELECT, block dangerous operations        |
| **Input**    | `sql: str`                                          |
| **Output**   | `True` if safe, `False` otherwise                   |
| **Checks**   | Starts with `select`, no forbidden keywords         |

**Forbidden keywords list:**
```python
["drop", "delete", "update", "insert",
 "alter", "truncate", "create", ";--"]
```

#### `clean_sql(sql: str) -> str`

| Attribute    | Value                                               |
| ------------ | --------------------------------------------------- |
| **Purpose**  | Strip markdown code fences from LLM output          |
| **Input**    | `sql: str` (possibly with ```` ```sql ``` ```` tags)|
| **Output**   | Clean SQL string                                    |
| **Method**   | Regex substitution + trim whitespace/semicolons     |

#### `process_query(request, db, _) -> dict`

| Attribute    | Value                                               |
| ------------ | --------------------------------------------------- |
| **Route**    | `POST /query`                                       |
| **Input**    | `QueryRequest{query: str}`                          |
| **Output**   | `{user_query, generated_sql, results, count}`      |
| **Depends**  | `get_db`, `verify_token`                            |
| **Raises**   | 400 (bad SQL), 401 (auth), 500 (internal)           |

---

## 5. Prompt Engineering

### 5.1 Prompt Template

```
You are a SQL query generator. Convert the user's natural language 
question into a PostgreSQL SELECT query.

Table schema:
customers (customer_id INTEGER PRIMARY KEY, name TEXT, gender TEXT, location TEXT)

Rules:
- Return ONLY the SQL query, no explanation, no markdown.
- Only SELECT queries are allowed.
- Use case-insensitive matching with ILIKE for text comparisons.

User question: {user_query}

SQL query:
```

### 5.2 Why This Prompt Works

```mermaid
graph LR
    A[Clear Role<br/>SQL generator] --> B[Schema Context<br/>Table structure]
    B --> C[Strict Rules<br/>No markdown, SELECT only]
    C --> D[Case Insensitive<br/>ILIKE hint]
    D --> E[Structured Format<br/>Question → SQL]
    E --> F[✅ Reliable Output]

    style F fill:#66bb6a,color:#fff
```

### 5.3 LLM Parameters

| Parameter     | Value                        | Why                                  |
| ------------- | ---------------------------- | ------------------------------------ |
| `model`       | `llama-3.1-8b-instant`       | Fast, capable, free tier             |
| `temperature` | `0.1`                        | Low = deterministic SQL output       |
| `messages`    | Single user message          | No chat history needed               |

---

## 6. End-to-End Execution Trace

### 6.1 Happy Path

```mermaid
sequenceDiagram
    participant U as User
    participant R as React
    participant F as FastAPI
    participant A as Auth
    participant L as Logger
    participant G as Groq
    participant C as clean_sql
    participant V as is_safe_sql
    participant D as PostgreSQL

    U->>R: Types "female customers from Mumbai"
    U->>R: Clicks "Ask"
    R->>F: POST /query<br/>{query: "..."}
    F->>A: verify_token(header)
    A-->>F: ✅ True
    F->>L: logger.info("Incoming query: ...")
    F->>F: Build prompt with schema
    F->>G: client.chat.completions.create(...)
    G-->>F: "```sql\nSELECT * FROM customers...\n```"
    F->>C: clean_sql(raw)
    C-->>F: "SELECT * FROM customers WHERE..."
    F->>L: logger.info("Generated SQL: ...")
    F->>V: is_safe_sql(sql)
    V-->>F: ✅ True
    F->>D: db.execute(text(sql))
    D-->>F: [Row(2, Priya, F, Mumbai), Row(7, Kavya, F, Mumbai)]
    F->>F: Convert rows to dicts
    F->>L: logger.info("Query returned 2 rows")
    F-->>R: {user_query, generated_sql, results, count}
    R->>R: setResponse(data)
    R->>R: Render table
    R-->>U: Shows 2 customers
```

### 6.2 Error Path: Unsafe SQL

```mermaid
sequenceDiagram
    participant U as User
    participant F as FastAPI
    participant G as Groq
    participant V as is_safe_sql
    participant L as Logger

    U->>F: POST /query<br/>{query: "delete all customers"}
    F->>G: Build prompt, send
    G-->>F: "DROP TABLE customers"
    F->>V: is_safe_sql("DROP TABLE...")
    V-->>F: ❌ False
    F->>L: logger.error("Unsafe SQL rejected")
    F-->>U: 400 Bad Request<br/>"Unsafe SQL rejected: DROP TABLE..."
```

---

## 7. Frontend Component (`App.js`)

### 7.1 State Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Typing: onChange
    Typing --> Idle: empty
    Typing --> Loading: onClick / Enter
    Loading --> Success: 200 OK
    Loading --> Error: 4xx/5xx
    Success --> Typing: new input
    Error --> Typing: new input
    Success --> [*]
    Error --> [*]
```

### 7.2 React State Variables

| State       | Type         | Purpose                            |
| ----------- | ------------ | ---------------------------------- |
| `query`     | `string`     | User's input text                  |
| `response`  | `object`     | API response (results + SQL)       |
| `loading`   | `boolean`    | Disables button during request     |
| `error`     | `string`     | Error message to display           |

### 7.3 Component Tree

```mermaid
graph TB
    App --> Container
    Container --> Header[h1: LLM Chatbot]
    Container --> Sub[p: subtitle]
    Container --> Input[Input Section]
    Container --> Ex[Examples Box]
    Container --> Err[Error Display]
    Container --> Res[Results Section]

    Input --> I1[query-input]
    Input --> I2[submit-btn]

    Res --> R1[SQL Preview]
    Res --> R2[Count]
    Res --> R3[Results Table]

    R3 --> T1[thead]
    R3 --> T2[tbody with rows]

    style App fill:#42a5f5,color:#fff
    style Container fill:#667eea,color:#fff
```

### 7.4 Key Functions

#### `handleSubmit()`
```javascript
const handleSubmit = async () => {
  if (!query.trim()) { setError('Please enter a query'); return; }
  setLoading(true); setError(''); setResponse(null);
  try {
    const res = await axios.post(API_URL,
      { query: query },
      { headers: { 'Content-Type': 'application/json',
                   'Authorization': `Bearer ${API_TOKEN}` }}
    );
    setResponse(res.data);
  } catch (err) {
    setError(err.response?.data?.detail || 'Something went wrong');
  } finally {
    setLoading(false);
  }
};
```

#### `handleKeyPress(e)`
Enables pressing `Enter` to submit — improves UX.

---

## 8. API Contract

### 8.1 OpenAPI Schema (simplified)

```mermaid
classDiagram
    class QueryRequest {
        +query: string
    }

    class QueryResponse {
        +user_query: string
        +generated_sql: string
        +results: array~object~
        +count: integer
    }

    class ErrorResponse {
        +detail: string
    }

    class CustomerRow {
        +customer_id: integer
        +name: string
        +gender: string
        +location: string
    }

    QueryResponse "1" --> "*" CustomerRow : contains
```

### 8.2 Status Code Contract

| Code | Meaning                  | When                                    |
| ---- | ------------------------ | --------------------------------------- |
| 200  | Success                  | Valid query, SQL executed               |
| 400  | Bad Request              | LLM generated unsafe SQL                |
| 401  | Unauthorized             | Missing or wrong Bearer token           |
| 422  | Validation Error         | Request body missing `query` field      |
| 500  | Internal Server Error    | LLM failure, DB error, unexpected crash |

---

## 9. Security Implementation

### 9.1 Defense in Depth

```mermaid
graph TB
    A[User Input] --> B[Layer 1: Bearer Token]
    B --> C[Layer 2: Pydantic Validation]
    C --> D[Layer 3: LLM Prompt Constraints]
    D --> E[Layer 4: SQL Cleaning]
    E --> F[Layer 5: SELECT Whitelist]
    F --> G[Layer 6: Keyword Blacklist]
    G --> H[Layer 7: Parameterized Execution]
    H --> I[✅ Query Executes Safely]

    style B fill:#ef5350,color:#fff
    style C fill:#ef5350,color:#fff
    style D fill:#ef5350,color:#fff
    style E fill:#ef5350,color:#fff
    style F fill:#ef5350,color:#fff
    style G fill:#ef5350,color:#fff
    style H fill:#ef5350,color:#fff
    style I fill:#66bb6a,color:#fff
```

### 9.2 Secret Management Flow

```mermaid
graph LR
    A[.env file<br/>git-ignored] --> B[load_dotenv]
    B --> C[os.getenv]
    C --> D[Groq client init]
    C --> E[DB connection]
    C --> F[Token comparison]

    G[.env.example<br/>committed] -.template.-> A

    style A fill:#ef5350,color:#fff
    style G fill:#66bb6a,color:#fff
```

---

## 10. Logging Strategy

### 10.1 Log Points

```mermaid
graph LR
    A[Request In] -->|INFO| L1[logger]
    B[SQL Generated] -->|INFO| L1
    C[Rows Returned] -->|INFO| L1
    D[Unsafe SQL] -->|ERROR| L1
    E[Exception] -->|ERROR| L1
    L1 --> F[stdout/stderr]

    style L1 fill:#ffa726,color:#000
```

### 10.2 Log Format
```
2026-04-10 11:08:15,194 - INFO - Incoming query: Show me all female customers from Mumbai
2026-04-10 11:08:15,579 - INFO - Generated SQL: SELECT * FROM customers WHERE...
2026-04-10 11:08:15,581 - INFO - Query returned 2 rows
```

---

## 11. Testing Strategy

### 11.1 Manual Test Cases

| # | Test                    | Input                              | Expected                    |
| - | ----------------------- | ---------------------------------- | --------------------------- |
| 1 | Happy path              | "Show all customers"               | Returns all 7 rows          |
| 2 | Filter by gender        | "List female customers"            | Returns 4 female rows       |
| 3 | Filter by location      | "Customers from Mumbai"            | Returns 3 Mumbai customers  |
| 4 | Combined filter         | "Male customers in Delhi"          | Returns Rohan Gupta         |
| 5 | Count query             | "How many customers in Bangalore"  | Returns count result        |
| 6 | No token                | Missing Authorization header       | 401 Unauthorized            |
| 7 | Wrong token             | `Bearer wrong`                     | 401 Unauthorized            |
| 8 | Empty query             | `{"query": ""}`                    | Error message in UI         |
| 9 | Malicious query         | "Delete all customers"             | 400 Unsafe SQL rejected     |

### 11.2 cURL Test Commands

```bash
# Test 1: Happy path
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mysecrettoken123" \
  -d '{"query": "Show all customers"}'

# Test 6: No token
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all customers"}'
# Expected: 401
```

---

## 12. Deployment Steps

```mermaid
graph TB
    A[Clone repo] --> B[Install PostgreSQL]
    B --> C[Create DB & user]
    C --> D[cd backend]
    D --> E[venv + pip install]
    E --> F[cp .env.example .env]
    F --> G[Add Groq key to .env]
    G --> H[python seed.py]
    H --> I[uvicorn main:app --reload]
    I --> J[cd frontend]
    J --> K[npm install]
    K --> L[npm start]
    L --> M[✅ Open localhost:3000]

    style M fill:#66bb6a,color:#fff
```

---

## 13. Dependencies

### 13.1 Backend (`requirements.txt`)
| Package          | Version  | Purpose                        |
| ---------------- | -------- | ------------------------------ |
| fastapi          | ≥0.135   | Web framework                  |
| uvicorn          | ≥0.44    | ASGI server                    |
| sqlalchemy       | ≥2.0     | ORM                            |
| psycopg2-binary  | ≥2.9     | PostgreSQL driver              |
| groq             | ≥1.1     | Groq LLM client                |
| python-dotenv    | ≥1.2     | Load .env files                |
| pydantic         | ≥2.12    | Request validation             |

### 13.2 Frontend (`package.json`)
| Package | Purpose                   |
| ------- | ------------------------- |
| react   | UI library                |
| axios   | HTTP client               |

---

## 14. Conclusion

This LLD has walked through every class, function, API contract, and data flow in the system. Combined with the [HLD](./HLD.md), any developer should be able to understand, maintain, and extend this chatbot with confidence.

**Key takeaways:**
- **Simple layered architecture** (Frontend → API → LLM → DB)
- **Security-first design** (7-layer defense)
- **Observability built-in** (structured logging at every step)
- **Extensible** (add tables, new endpoints, more complex queries)
