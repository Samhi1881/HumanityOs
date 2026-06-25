# Local Development Setup & Installation Guide

Follow this guide to install, configure, and run the HumanityOS platform locally on your development machine.

---

## 📋 Prerequisites

Ensure you have the following software installed:
* **Node.js** (v20.x or higher)
* **Python** (v3.11.x)
* **PostgreSQL** (v16)
* **Redis** (v7)
* **ChromaDB** (Native or containerized)
* **Docker & Docker Compose** (Optional, for running localized containers)

---

## 🛠️ Backend Installation

### 1. Set Up Virtual Environment
Navigate to the `/backend` directory and create a Python virtual environment:
```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:
* **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
* **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

### 2. Install Dependencies
Install all pinned dependencies, including Alembic and database libraries:
```bash
pip install -r requirements.txt
```

### 3. Configure Local Environment Variables
Create a local `.env` configuration file from the template:
```bash
cp .env.template .env
```
Open `.env` and fill out the details:
```ini
ENV=development
DEBUG=True
PORT=8080
SECRET_KEY=local_development_secret_key_change_me
DATABASE_URL=postgresql+asyncpg://humanity:humanity_password@localhost:5432/humanityos
REDIS_URL=redis://localhost:6379/0
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
GEMINI_API_KEY=your_gemini_api_key_here
FIREBASE_PROJECT_ID=humanityos-prod
RATE_LIMIT_PER_MINUTE=60
```

### 4. Run Database Migrations
Initialize and upgrade your database schema using Alembic:
```bash
alembic upgrade head
```

### 5. Launch the Backend Server
Start the FastAPI server in development reload mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```
The interactive Swagger API documentation will be available at `http://localhost:8080/docs`.

---

## 💻 Frontend Installation

### 1. Install Node Dependencies
Navigate to the `/frontend` directory and install packages using `npm`:
```bash
cd ../frontend
npm install
```

### 2. Configure Client Environment Variables
Create a `.env` file in the frontend folder:
```bash
cp .env.template .env
```
Verify the backend endpoint points to your local server:
```ini
VITE_API_URL=http://localhost:8080/api/v1
```

### 3. Launch the React Client
Start the Vite development web server:
```bash
npm run dev
```
Open your browser and navigate to `http://localhost:3000` (or the port specified by Vite) to view the Command Center Dashboard.

---

## 🧪 Validating the Installation

### 1. Run Backend Pytests
To ensure all security guards, rate limit policies, and agent pipelines function, run the pytest suite inside the active backend environment:
```bash
cd backend
.venv\Scripts\pytest
```

### 2. Run Frontend Typechecks
To ensure TS safety before deployment, verify the compilation builds:
```bash
cd frontend
npm run typecheck
```
Both validations should complete successfully with zero errors.
