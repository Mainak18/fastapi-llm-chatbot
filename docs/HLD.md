# 📘 High-Level Design (HLD)
## LLM-Powered Chatbot with FastAPI & PostgreSQL

**Project:** FastAPI + LLM Chatbot Challenge  
**Author:** Mainak Bhattacharjee
**Version:** 1.0  
**Date:** April 2026

---

## 1. Introduction

### 1.1 Purpose
This document describes the high-level architecture of an intelligent chatbot system that converts natural language queries into SQL and retrieves data from a relational database. The system uses a Large Language Model (LLM) hosted by Groq to interpret user intent.

### 1.2 Scope
The system allows non-technical users to query a customer database using plain English instead of writing SQL. It returns structured, tabular results through a web interface.

### 1.3 Target Audience
- Developers maintaining the system
- Reviewers evaluating the project
- Stakeholders understanding the design

---

## 2. System Overview

### 2.1 Context Diagram

```mermaid
graph TB
    subgraph "External Actors"
        U[👤 End User]
        G[🤖 Groq LLM Service]
    end

    subgraph "Chatbot System"
        S[🖥️ Chatbot Application]
    end

    subgraph "Data Storage"
        D[(🐘 PostgreSQL)]
    end

    U -->|Natural language queries| S
    S -->|Formatted results| U
    S -->|Prompts| G
    G -->|Generated SQL| S
    S <-->|Read queries| D

    style U fill:#f9a825,color:#000
    style S fill:#667eea,color:#fff
    style G fill:#ab47bc,color:#fff
    style D fill:#26a69a,color:#fff
```

### 2.2 Key Objectives
1. **Accessibility** — Enable non-technical users to query data without SQL knowledge
2. **Accuracy** — Generate correct SQL from varied natural language phrasings
3. **Security** — Prevent SQL injection and unauthorized access
4. **Performance** — Respond within 2-3 seconds per query
5. **Maintainability** — Modular, well-documented codebase

---

## 3. Architectural Design

### 3.1 Three-Tier Architecture

```mermaid
graph TB
    subgraph "Presentation Tier"
        UI[⚛️ React SPA<br/>Port 3000]
    end

    subgraph "Application Tier"
        API[⚡ FastAPI Server<br/>Port 8000]
        MW[🔒 Auth Middleware]
        BL[🧠 Business Logic]
        VAL[🛡️ SQL Validator]
    end

    subgraph "Data Tier"
        DB[(🐘 PostgreSQL<br/>Port 5432)]
    end

    subgraph "External Tier"
        LLM[🤖 Groq API]
    end

    UI -.HTTPS/CORS.-> API
    API --> MW
    MW --> BL
    BL --> LLM
    BL --> VAL
    VAL --> DB
    DB --> BL
    BL --> API
    API -.JSON.-> UI

    style UI fill:#42a5f5,color:#fff
    style API fill:#66bb6a,color:#fff
    style MW fill:#ef5350,color:#fff
    style BL fill:#ffa726,color:#000
    style VAL fill:#ef5350,color:#fff
    style DB fill:#26a69a,color:#fff
    style LLM fill:#ab47bc,color:#fff
```

### 3.2 Layer Responsibilities

| Layer            | Responsibility                                                |
| ---------------- | ------------------------------------------------------------- |
| **Presentation** | UI rendering, user input capture, result display              |
| **Application**  | Request routing, authentication, LLM interaction, validation  |
| **Data**         | Persistent storage of customer records, query execution       |
| **External**     | Natural language to SQL conversion (Groq)                     |

---

## 4. Component Diagram

```mermaid
graph LR
    subgraph "Frontend Components"
        A[QueryInput]
        B[SubmitButton]
        C[ResultsTable]
        D[ErrorDisplay]
        E[SQLPreview]
    end

    subgraph "Backend Components"
        F[Auth Handler]
        G[Query Endpoint]
        H[LLM Client]
        I[SQL Sanitizer]
        J[DB Session Manager]
        K[Logger]
    end

    subgraph "Database"
        L[(customers table)]
    end

    A --> B
    B --> G
    G --> F
    F --> H
    H --> I
    I --> J
    J --> L
    L --> J
    J --> G
    G --> C
    G --> E
    G --> D
    G --> K

    style A fill:#42a5f5,color:#fff
    style B fill:#42a5f5,color:#fff
    style C fill:#42a5f5,color:#fff
    style D fill:#42a5f5,color:#fff
    style E fill:#42a5f5,color:#fff
    style F fill:#66bb6a,color:#fff
    style G fill:#66bb6a,color:#fff
    style H fill:#66bb6a,color:#fff
    style I fill:#66bb6a,color:#fff
    style J fill:#66bb6a,color:#fff
    style K fill:#66bb6a,color:#fff
    style L fill:#26a69a,color:#fff
```

---

## 5. Data Flow Diagram

### 5.1 Level 0 (Context)

```mermaid
graph LR
    U[User] -->|Query| S[Chatbot System]
    S -->|Results| U
    S -->|Prompt| L[LLM]
    L -->|SQL| S
    S <-->|Data| D[(Database)]

    style U fill:#f9a825,color:#000
    style S fill:#667eea,color:#fff
    style L fill:#ab47bc,color:#fff
    style D fill:#26a69a,color:#fff
```

### 5.2 Level 1 (Detailed)

```mermaid
graph TB
    U[👤 User] -->|1. Natural language| F[⚛️ Frontend]
    F -->|2. HTTP POST + Token| A[🔐 Auth Layer]
    A -->|3. Validated| P[📝 Prompt Builder]
    P -->|4. Prompt with schema| L[🤖 Groq LLM]
    L -->|5. Raw SQL| C[🧹 SQL Cleaner]
    C -->|6. Clean SQL| V[🛡️ Safety Validator]
    V -->|7. Approved SQL| E[⚙️ Query Executor]
    E -->|8. SQL| D[(🐘 PostgreSQL)]
    D -->|9. Rows| E
    E -->|10. JSON results| F
    F -->|11. Rendered table| U

    style U fill:#f9a825,color:#000
    style F fill:#42a5f5,color:#fff
    style A fill:#ef5350,color:#fff
    style P fill:#ffa726,color:#000
    style L fill:#ab47bc,color:#fff
    style C fill:#ffa726,color:#000
    style V fill:#ef5350,color:#fff
    style E fill:#66bb6a,color:#fff
    style D fill:#26a69a,color:#fff
```

---

## 6. Technology Stack

### 6.1 Stack Choices & Rationale

```mermaid
mindmap
  root((Chatbot))
    Backend
      FastAPI
        Async support
        Auto Swagger docs
        Type hints
      Python 3.12
        Rich ecosystem
        LLM libraries
    Frontend
      React 18
        Component model
        Virtual DOM
      Axios
        Promise-based HTTP
    Database
      PostgreSQL 16
        ACID compliance
        Production grade
        ILIKE support
      SQLAlchemy 2.0
        ORM abstraction
        Connection pooling
    LLM
      Groq Cloud
        Free tier
        Fast inference
      Llama 3.1 8B
        Open weights
        Good SQL skills
```

### 6.2 Why These Choices?

| Choice          | Why                                                             |
| --------------- | --------------------------------------------------------------- |
| **FastAPI**     | Modern, async, automatic Swagger/OpenAPI docs                   |
| **PostgreSQL**  | Production-grade; chose over SQLite for real-world quality      |
| **React**       | Most popular frontend library, component-based architecture     |
| **Groq**        | Free tier, extremely fast inference (~300 tokens/sec)           |
| **Llama 3.1**   | Strong at code/SQL generation, open weights, reliable           |
| **SQLAlchemy**  | Industry-standard Python ORM, type-safe queries                 |

---

## 7. Key Design Decisions

### 7.1 Why Natural Language → SQL (not direct query)?
- Allows non-technical users to access data
- Reduces need for custom API endpoints per query type
- Flexible: new queries don't require code changes

### 7.2 Why SELECT-only?
- Prevents destructive operations by malicious users
- LLMs can hallucinate or be tricked into generating harmful SQL
- Read-only guarantees data integrity

### 7.3 Why Bearer Token (not OAuth)?
- Simpler for an assignment/demo
- Meets "optional token-based check" requirement
- OAuth would be overkill for this scope

### 7.4 Why PostgreSQL over SQLite?
- Demonstrates production readiness
- Case-insensitive `ILIKE` operator (SQLite lacks this natively)
- Better concurrency for future scaling

---

## 8. Non-Functional Requirements

| Category            | Requirement                                           |
| ------------------- | ----------------------------------------------------- |
| **Performance**     | Response < 3 seconds per query                        |
| **Availability**    | 99% uptime (dev target)                               |
| **Security**        | Token auth + SQL injection prevention                 |
| **Usability**       | Clean UI, example queries shown to user               |
| **Maintainability** | Modular code, documented, .env config                 |
| **Scalability**     | Stateless backend (can be horizontally scaled)        |
| **Observability**   | Structured logging of all queries                     |

---

## 9. Deployment Topology (Current - Local Dev)

```mermaid
graph TB
    subgraph "Developer Machine (Ubuntu Linux)"
        subgraph "Terminal 1"
            T1[uvicorn main:app<br/>Port 8000]
        end
        subgraph "Terminal 2"
            T2[npm start<br/>Port 3000]
        end
        subgraph "System Service"
            PG[postgresql.service<br/>Port 5432]
        end
    end

    subgraph "Internet"
        GR[Groq API<br/>api.groq.com]
    end

    B[Browser<br/>localhost:3000] --> T2
    T2 --> T1
    T1 --> PG
    T1 -.HTTPS.-> GR

    style T1 fill:#66bb6a,color:#fff
    style T2 fill:#42a5f5,color:#fff
    style PG fill:#26a69a,color:#fff
    style GR fill:#ab47bc,color:#fff
    style B fill:#f9a825,color:#000
```

---

## 10. Future Enhancements

```mermaid
graph LR
    A[Current MVP] --> B[Phase 2]
    A --> C[Phase 3]
    A --> D[Phase 4]

    B --> B1[Query history]
    B --> B2[User accounts]
    B --> B3[Favorites]

    C --> C1[Multi-table support]
    C --> C2[Chart visualizations]
    C --> C3[Export to CSV]

    D --> D1[Docker deployment]
    D --> D2[CI/CD pipeline]
    D --> D3[Cloud hosting]

    style A fill:#66bb6a,color:#fff
    style B fill:#42a5f5,color:#fff
    style C fill:#ab47bc,color:#fff
    style D fill:#ffa726,color:#000
```

---

## 11. Risks & Mitigations

| Risk                               | Impact | Mitigation                          |
| ---------------------------------- | ------ | ----------------------------------- |
| LLM generates invalid SQL          | Medium | SQL validator rejects bad queries   |
| LLM generates harmful SQL          | High   | Whitelist SELECT only               |
| Groq API rate limit hit            | Low    | Free tier is generous for demo      |
| API key leaked                     | High   | `.env` git-ignored, rotatable       |
| Database downtime                  | Medium | Try/except around DB calls          |
| User types nonsense query          | Low    | Returns empty results gracefully    |

---

## 12. Conclusion

This HLD outlines a clean, secure, three-tier architecture leveraging modern tools (FastAPI, React, PostgreSQL) and cutting-edge LLM technology (Groq's Llama 3.1). The design prioritizes security, usability, and maintainability while meeting all functional requirements of the challenge.

For implementation details, see the [Low-Level Design document](./LLD.md).
