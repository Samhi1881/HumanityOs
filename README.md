# HumanityOS: Humanitarian Operations Command Center

HumanityOS is a next-generation, production-ready Command Center platform designed to orchestrate cognitive AI agents, parse spatial disaster maps, simulate crises, and authorize responders during humanitarian relief operations.

![HumanityOS Dashboard Preview](docs/assets/humanityos_dashboard.png)

## Core Capabilities
* **Interactive Disaster Map**: Rich geographic rendering of emergency zones, hospital availability, shelter capacity, and real-time responder coordinates.
* **Agent Execution Graph**: A visual canvas powered by **React Flow** demonstrating the live status, communication flows, and confidence scores of 11 AI specialist agents.
* **Disaster Simulation Engine**: Real-time simulation of five complex crisis scenarios (Cyclone, Flood, Earthquake, Wildfire, Heatwave) triggering cascades of emergency updates.
* **Granular Security (RBAC & Auth)**: Strict Firebase Authentication with 5 user roles (Administrator, Responder, Volunteer, NGO, Citizen) protecting agent execution and rate limits.
* **Cognitive Decision Auditor**: Security-bound auditing system ensuring disaster proposals comply with safety bounds and accessibility guidelines.

---

## 🏗️ Architecture & System Diagrams

Below are the key architectural diagrams mapping the data flows, agent pipelines, and protocols within HumanityOS.

### 1. Central Component Topology (Core Architecture)
Maps the relationship between the React client, FastAPI gateway, caches, databases, and LLM providers.

```mermaid
graph TD
    User([Responder / Operator]) -->|Interacts| FE[React Web App]
    FE -->|API Queries| BE[FastAPI Gateway]
    
    subgraph "Backend Services Layer"
        BE -->|Async DB Sessions| DB[(PostgreSQL)]
        BE -->|Cache & Rate Limit| Cache[(Redis Cache)]
        BE -->|Document Search| Vector[(ChromaDB)]
        BE -->|Cognitive Runs| AgentGroup[Orchestrator & Specialists]
    end

    subgraph "External Integrations"
        AgentGroup -->|Generative Text| Gemini[Google Gemini API]
        AgentGroup -->|Dynamic Tools| MCP[External MCP Servers]
    end
```

![HumanityOS Core Components Architecture](docs/assets/humanityos_architecture.png)

---

### 2. Cognitive Agent Interaction (Sequence Diagram)
Shows the sequential and parallel message passing over the global `EventBus` and `SharedMemory` interface.

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Command Operator
    participant Commander as Commander Agent
    participant Specialists as Specialist Agents
    participant Auditor as Decision Auditor
    participant Bus as Event Bus

    Operator->>Commander: Triggers Incident (e.g., Flood Alert)
    Commander->>Bus: Publishes "IncidentDetected"
    Note over Specialists: Specialists check topic subscriptions
    
    par Parallel Specialist Run
        Bus-->>Specialists: Receives Incident Data
        Specialists->>Specialists: Analyze (Weather, Medical, Vol, Shelter)
        Specialists->>Commander: Returns recommendations & confidence scores
    end

    Commander->>Commander: Aggregates observations & runs replanning
    Commander->>Auditor: Submits aggregate rescue proposal
    
    alt Safety & Guidelines Compliant
        Auditor->>Commander: returns Status: SAFE
        Commander->>Operator: Serves finalized proposal
    else Accessibility / Safety Violations Detected
        Auditor->>Commander: returns Status: WARN (reasons listed)
        Commander->>Commander: Re-evaluates resources (fallback path)
        Commander->>Operator: Serves audit alerts & alternate proposal
    end
```

![Cognitive Agent Interaction Pipeline](docs/assets/agent_interaction.png)

---

### 3. ADK Model & Workflow (State Diagram)
Demonstrates how the Agent Development Kit (ADK) guides specialist node execution, event loops, and memory logging.

```mermaid
stateDiagram-v2
    [*] --> Initialization : Define Specialist Class
    Initialization --> RegisterSubscriptions : Bind to EventBus Topics
    
    state PipelineExecution {
        [*] --> IngestEvent : Listen on Subscribed Topic
        IngestEvent --> ScanState : Read SharedMemoryState Records
        ScanState --> QueryVectorStore : Search context details (ChromaDB)
        QueryVectorStore --> PromptGeneration : Construct Specialist prompt
        PromptGeneration --> GeminiInference : Request LLM Generation
        GeminiInference --> ValidationCheck : Enforce confidence score thresholds
    }

    ValidationCheck --> WriteMemory : Write recommendations to Shared Memory
    WriteMemory --> PublishEvent : Publish result event to Bus (e.g., "ShelterFull")
    PublishEvent --> [*]
```

![ADK Node Workflow Pipeline](docs/assets/adk_workflow.png)

---

### 4. Model Context Protocol (MCP) Integration
Maps how external LLM clients fetch tools from the FastAPI Server using Server-Sent Events (SSE).

```mermaid
graph LR
    subgraph "FastAPI Server App"
        SSE[SSE Transport Mount]
        Server[MCP Server instance]
        ToolRegistry[Tool Registry]
        
        SSE --- Server
        Server --- ToolRegistry
    end
    
    subgraph "Active Client"
        Client[LLM Agent Runner]
        Client -->|Requests Tool list| SSE
        Client -->|Invokes Tool command| SSE
    end
    
    ToolRegistry -->|Read/Write| DB[(Postgres / Chroma)]
    ToolRegistry -->|Trigger| Script[Local Automation Tools]
```

![Model Context Protocol (MCP) Architecture](docs/assets/mcp_architecture.png)

---


## Technical Documentation Portal

Browse the technical guides to set up, operate, deploy, and present the HumanityOS platform:

### 1. Development & Setup Guides
* 💻 **[Local Installation Guide](docs/installation_guide.md)**: Setup PostgreSQL, Redis, ChromaDB, FastAPI dependencies, and the React Vite client on your local machine.
* 📦 **[Deployment Guide](docs/deployment_guide.md)**: Containerize the app and deploy the backend to **Google Cloud Run** and the frontend to **Firebase Hosting** using automatic GitHub Actions CI/CD workflows.

### 2. Architecture & Design Specifications
* 🏗️ **[System Architecture & Workflows](docs/architecture_documentation.md)**: Conceptual layout of the cognitive agent hierarchy, Model Context Protocol (MCP) server integration, and ADK model declaration workflows.
* 🗄️ **[Database Schema Layout](docs/database_schema.md)**: Specifications for PostgreSQL relational schemas, Alembic migrations, Chroma vector collections, and Redis key structures.
* 🔌 **[API Documentation](docs/api_documentation.md)**: Path specifications, request validation models, response payloads, role access mappings, and rate limits.

### 3. Verification, Demos & Presentation
* 🎤 **[Hackathon Presentation & Demo Script](docs/demo_script.md)**: A complete 5-minute demo walkthrough, slide deck outline, and script operators prompts for pitching.
* 🔧 **[Troubleshooting Guide](docs/troubleshooting_guide.md)**: Steps to diagnose and resolve typical database, Redis, Firebase, and LLM runtime warnings.

---

## High-Level Folder Structure

```
humanityos/
├── .github/
│   └── workflows/
│       ├── deploy.yml            # CI/CD (Tests, builds, pushes to Cloud Run/Firebase)
│       ├── backend-ci.yml        # Backend automated tests run
│       └── frontend-ci.yml       # Frontend TypeScript validation
├── backend/
│   ├── app/
│   │   ├── agents/               # Multi-agent architecture (specialists, commander, auditor)
│   │   ├── api/                  # API routers (endpoints, simulation engine)
│   │   ├── core/                 # Settings (config, security checks, logging)
│   │   ├── db/                   # Async session engine provider
│   │   ├── models/               # Declarative SQLAlchemy models base
│   │   ├── schemas/              # Input/output validation structures
│   │   └── services/             # SOLID business services (AI, Vector, Cache, MCP)
│   ├── alembic/                  # Alembic migration scripts
│   ├── tests/                    # Backend Pytest unit tests
│   ├── Dockerfile                # Secure non-root runner multi-stage image
│   ├── start.sh                  # Startup check, migration runner, and server uvicorn run
│   └── pyproject.toml            # Python lint and test configs
├── frontend/
│   ├── src/
│   │   ├── features/
│   │   │   ├── flow/             # React Flow execution graph canvas
│   │   │   └── map/              # Leaflet spatial disaster mapping
│   │   ├── services/             # Client API networking endpoints
│   │   └── App.tsx               # Main Command Center UI Dashboard
│   ├── Dockerfile                # Production Nginx SPA serving image
│   ├── nginx.conf                # Nginx router, gzip, and security headers config
│   └── tailwind.config.js        # Design styling configs
├── docker-compose.prod.yml       # Production-ready local multi-container coordinator
├── cloudbuild.yaml               # Google Cloud Build build & deploy sequence
└── firebase.json                 # Firebase Hosting configurations
```
