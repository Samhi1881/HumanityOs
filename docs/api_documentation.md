# API Reference Documentation

This document specifies the endpoints, request payloads, response formats, role-based access control (RBAC), and security guards implemented on the HumanityOS backend.

---

## 🔒 Security Summary
* **Authentication**: Enforced via standard JWT validation (custom Firebase credentials verification).
* **Rate Limiting**: Configured to 60 requests per minute per IP. Returns `429 Too Many Requests`.
* **Prompt Injection Scanner**: Applies keyword scanning to POST request strings. Returns `400 Bad Request` if suspicious prompts (e.g. "ignore previous instructions") are detected.

---

## 🛰️ 1. System Status Endpoints

### `GET /api/v1/status`
Retrieves the operational status of the database and Redis cache.

* **Authorization**: Open to all roles (`Administrator`, `Emergency Responder`, `Volunteer`, `NGO`, `Citizen`).
* **Rate Limited**: Yes.
* **Response Payload (`200 OK`)**:
  ```json
  {
    "status": "online",
    "database": "connected",
    "cache": "healthy"
  }
  ```

---

## 🧠 2. AI & Context Endpoints

### `POST /api/v1/query-ai`
Submits a query prompt, retrieves relevant contexts from the Chroma vector store, and triggers a text generation call with Google Gemini.

* **Authorization**: Restricted to `Administrator`, `Emergency Responder`, `Volunteer`, and `NGO` roles.
* **Rate Limited**: Yes.
* **Security Guards**: Scans for prompt injection attacks.
* **Request Payload**:
  ```json
  {
    "prompt": "Provide the shelter capacity accessibility rules for Sector Alpha."
  }
  ```
* **Response Payload (`200 OK`)**:
  ```json
  {
    "response": "According to Sector Alpha guidelines, all shelters must provide wheel-chair ramp access and dedicated service dog areas...",
    "source": "scaffold_mock"
  }
  ```

---

## 🤖 3. Cognitive Agent Endpoints

### `POST /api/v1/agents/orchestrate`
Triggers the sequential and parallel execution of the 11 specialists. Commander consolidates the data, submits it to the Decision Auditor, and generates a safety and compliance evaluation.

* **Authorization**: Restricted to `Administrator` and `Emergency Responder` roles.
* **Rate Limited**: Yes.
* **Security Guards**: Scans for prompt injection attacks.
* **Request Payload**:
  ```json
  {
    "prompt": "Coordinate immediate response for Oakland Hills Wildfire corridor."
  }
  ```
* **Response Payload (`200 OK`)**:
  ```json
  {
    "status": "success",
    "prompt": "Coordinate immediate response for Oakland Hills Wildfire corridor.",
    "agent_responses": {
      "IncidentAnalysisAgent": {
        "status": "success",
        "confidence_score": 0.95,
        "data": { "critical_sectors": ["Sector Alpha", "Sector Beta"] }
      },
      "WeatherAgent": {
        "status": "success",
        "confidence_score": 0.90,
        "data": { "temperature_f": 75.0, "wind_speed_mph": 22.5 }
      },
      "DecisionAuditor": {
        "status": "success",
        "confidence_score": 0.98,
        "reasons": ["ADA checks passed", "Safety buffer confirmed"]
      }
    },
    "audit_report": {
      "status": "success",
      "confidence_score": 0.95,
      "reasons": ["All checks completed successfully."]
    },
    "captured_events": [
      { "event_type": "IncidentDetected", "source_agent": "CommanderAgent" }
    ]
  }
  ```

---

## 🌪️ 4. Disaster Simulation Endpoints

### `GET /api/v1/simulation/scenarios`
Lists all available pre-configured disaster simulation scenarios.

* **Authorization**: Restricted to `Administrator`, `Emergency Responder`, and `Volunteer` roles.
* **Rate Limited**: Yes.
* **Response Payload (`200 OK`)**:
  ```json
  [
    {
      "id": "cyclone",
      "name": "Cyclone Landfall",
      "description": "Category 4 cyclone impact simulation."
    },
    {
      "id": "flood",
      "name": "Atmospheric River Flood",
      "description": "High precipitation flooding simulation."
    }
  ]
  ```

### `GET /api/v1/simulation/scenarios/{id}`
Retrieves the step-by-step trigger data, map coordinates, and capacity thresholds for a specific scenario.

* **Authorization**: Restricted to `Administrator`, `Emergency Responder`, and `Volunteer` roles.
* **Rate Limited**: Yes.
* **Response Payload (`200 OK`)**:
  ```json
  {
    "id": "cyclone",
    "name": "Cyclone Landfall",
    "centerCoords": [37.7749, -122.4194],
    "steps": [
      {
        "step": 0,
        "title": "Storm Warning",
        "description": "Cyclone Category 4 warnings issued.",
        "event_type": "WeatherAlert",
        "source_agent": "WeatherAgent",
        "payload": { "wind_speed": 115.0, "warning_level": "RED" }
      }
    ]
  }
  ```

---

## 🔌 5. Model Context Protocol Endpoints

### `GET /api/v1/mcp/tools`
Retrieves available developer automation tools registered on the server.

* **Authorization**: Restricted to `Administrator` and `Emergency Responder` roles.
* **Rate Limited**: Yes.
* **Response Payload (`200 OK`)**:
  ```json
  {
    "tools": [
      {
        "name": "dispatch_resource",
        "description": "Sends emergency water/medical supplies to a sector."
      }
    ]
  }
  ```
