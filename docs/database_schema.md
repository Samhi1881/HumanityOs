# Database Schema Layout

This document describes the structure and schemas of the database, vector store, and caching layers in HumanityOS.

---

## 🗄️ 1. Relational Database (PostgreSQL)

HumanityOS utilizes PostgreSQL as its primary transactional store. Connections are managed asynchronously using SQLAlchemy 2.0 asyncpg drivers.

### Base Declarative Model
All tables inherit from the `Base` class and utilize `TimestampMixin` to enforce creation and update auditing:

```python
class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
```

### Alembic Migration Tracker Table
Alembic maintains table tracking in an internal metadata table:

#### Table Name: `alembic_version`
| Column Name | Data Type | Primary Key | Description |
| :--- | :--- | :---: | :--- |
| **version_num** | `VARCHAR(32)` | Yes | Revision hash tracking the current schema state (e.g. `001_initial`). |

---

## 📂 2. Vector Store Database (ChromaDB)

ChromaDB stores unstructured text data and documents (accessibility guidelines, disaster SOPs, and hospital details) to enable Retrieval-Augmented Generation (RAG) for specialists.

### Collection: `humanity_docs`
Stores standard operating procedures and response guidelines.

* **Id Field**: String (e.g. `doc-uuid-1234`)
* **Document Field**: Text string containing raw guidelines.
* **Embeddings**: Automatic vectors created using native Chroma/Gemini embeddings.
* **Metadata Fields**:
  ```json
  {
    "category": "accessibility",
    "incident_type": "flood",
    "importance": "high"
  }
  ```

---

## ⚡ 3. Caching & Rate Limiting (Redis)

Redis manages temporary, high-speed key-value caches and tracks IP requests to enforce API rate limits.

### Rate Limiter Key Layout
Protects API routes from abusive traffic.
* **Key Format**: `rate_limit:<ip_address>:<route_path>`
* **Data Type**: `String` (Integer counter incremented by Redis pipeline)
* **TTL (Time to Live)**: `60 seconds`
* **Limitation Behavior**: If the integer value exceeds `RATE_LIMIT_PER_MINUTE`, subsequent requests return a `429 Too Many Requests` error.

### Cache Key Layout
Used for caching system health status checks and transient LLM data.
* **Key Format**: `healthcheck`
* **Data Type**: `String`
* **TTL**: `10 seconds`

### Local In-Memory Fallback Schema
If Redis is offline, rate limiting switches to an in-memory dictionary.
* **Data Structure**: `dict[ip_address, list[timestamps]]`
* **Cleanup Routine**: Before processing, timestamps older than 60 seconds are removed from the list.
