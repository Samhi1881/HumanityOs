# HumanityOS Simulation & Security Tasks

- `[x]` Implement Backend Simulation Router (`backend/app/api/v1/simulation.py`)
  - `[x]` Define scenario structures for Cyclone, Flood, Earthquake, Wildfire, Heatwave
  - `[x]` Create endpoint `/api/v1/simulation/scenarios`
- `[x]` Mount Simulation Router in API (`backend/app/api/v1/endpoints.py`)
- `[x]` Implement Simulation Interface in Frontend (`frontend/src/App.tsx`)
  - `[x]` Add Scenario selector dropdown
  - `[x]` Add "Start Simulation" button with interactive control loop
  - `[x]` Wire simulation steps to trigger real-time updates on Map, Flow Canvas, Feed, Capacities, and Resources
  - `[x]` Wire final simulation step to trigger real agent orchestration API and Auditor panel results
- `[x]` Verify system builds and runs successfully
  - `[x]` Run `.venv\Scripts\pytest` to verify backend integrity
  - `[x]` Run `npm run typecheck` to verify frontend TypeScript safety

## Security Integration Tasks

- `[x]` Implement Backend Security Core (`backend/app/core/security.py`)
  - `[x]` Create Firebase Auth JWT verifier with development mock fallback
  - `[x]` Create RoleChecker for 5 Roles (Admin, Responder, Volunteer, NGO, Citizen)
  - `[x]` Create Prompt Injection scan pattern checker
  - `[x]` Create RateLimiter with Redis/in-memory fallback
  - `[x]` Integrate structured Audit Logging
- `[x]` Update Backend configuration settings (`backend/app/core/config.py`)
- `[x]` Apply security to API Routes (`backend/app/api/v1/endpoints.py` and `simulation.py`)
- `[x]` Integrate role simulation in frontend UI (`frontend/src/App.tsx` and `services/api.ts`)
- `[x]` Verify security validation results via pytest and typechecking
