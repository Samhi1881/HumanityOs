# HumanityOS System Architecture & Workflows

This document outlines the software architecture, agent hierarchies, cognitive interaction workflows, and Model Context Protocol (MCP) systems governing HumanityOS.

---

## 🏗️ Core Architecture Overview

HumanityOS is structured as a modular monorepo that separates cognitive orchestration, data caching, transactional memory, vector stores, and visual monitoring:

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

---

## 🤖 Cognitive Agent Hierarchy & Interaction Workflow

Cognitive orchestration is divided into a centralized orchestrator, specialized responder nodes, and a security audit check. The workflow runs through sequential gathering, parallel responder evaluations, and final compliance audits:

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

---

## 🛠️ ADK Model & Workflow Pipeline

The Agent Development Kit (ADK) guides how specialist agents declare models, register tasks, listen to the global event broker, and perform structured inference:

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

---

## 🔌 Model Context Protocol (MCP) Integration

The Model Context Protocol (MCP) enables LLMs to dynamically discover and call local or remote tools in a secure sandbox:

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

1. **SSE Transport Mount**: FastAPI mounts `/mcp` endpoints using Server-Sent Events (SSE) to facilitate streaming request-response loops.
2. **Tool Registry**: Declares active scripts and capabilities (e.g. check shelter occupancy, dispatch trucks) as JSON Schemas.
3. **Dynamic Invocation**: The client queries the schema list and invokes tools dynamically to resolve contextual gaps.
