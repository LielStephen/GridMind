# GridMind Architecture

GridMind is a reinforcement learning (RL) powered smart energy management simulator. It provides a simulation environment representing a building's thermal and energy systems, coupled with a React-based frontend dashboard for manual control and real-time visualization.

```mermaid
graph TD
    subgraph Frontend (React + Vite)
        Dashboard[React Dashboard] -->|API Requests| API_Client[useSimulation hook]
    end

    subgraph Backend (FastAPI + Gymnasium)
        API_Client -->|REST API| API_Server[FastAPI Server]
        API_Server -->|Reads / Steps| RL_Env[GridMindEnv Gymnasium Env]
        
        RL_Env -->|Simulates Device| HVAC[Air Conditioner Model]
        RL_Env -->|Simulates Device| Battery[Battery Storage Model]
        RL_Env -->|Reads Signals| Weather[Weather & Price Provider]
        
        Settings[Settings Dataclasses] -->|Configures| RL_Env
        
        PPO_Agent[PPO Agent Stable-Baselines3] -->|Trains on| RL_Env
    end
```

---

## Component Breakdown

### 1. Backend

*   **FastAPI Application (`backend/api/main.py`)**:
    Exposes REST endpoints to allow the frontend dashboard to step through, reset, and retrieve status from the simulator environment:
    *   `GET /`: Health check.
    *   `GET /simulation/state`: Reads the current observation vector without advancing the simulation.
    *   `POST /simulation/reset`: Resets the environment to a new 24-hour episode (96 steps of 15 minutes).
    *   `POST /simulation/step`: Steps the simulator forward by one timestep with a specified action.

*   **Gymnasium Environment (`backend/rl/env.py`)**:
    Implements a custom Gymnasium environment (`GridMind/Energy-v0`) that:
    *   Tracks the building indoor temperature and battery State of Charge (SOC).
    *   Computes rewards as the negative sum of utility costs and comfort penalties.
    *   Manages transition logic at each 15-minute timestep.

*   **Physical Simulators (`backend/simulator/models.py`)**:
    Houses the low-level modeling classes for the physical components:
    *   `AirConditioner`: Computes cooling rates and electrical consumption when ON/OFF.
    *   `Battery`: Simulates round-trip efficiency, charging constraints, and SOC updates.
    *   `WeatherProvider`: Models daily outdoor temperatures, solar irradiance profile, and time-of-use pricing (peak vs. off-peak rates).

*   **Configuration (`backend/config/settings.py`)**:
    Defines frozen dataclasses containing all default configuration constants (e.g., HVAC capacity, battery sizes, price tariffs, comfort bands, and PPO training hyperparameters).

---

## 2. Frontend

*   **React Dashboard (`frontend/src/`)**:
    *   Uses **Recharts** to plot outdoor temperature vs. indoor temperature, solar generation, electricity pricing, and battery SOC over time.
    *   Uses **Lucide React** icons to build a sleek modern energy telemetry dashboard.
    *   Allows manual interaction to test actions (Idle, AC ON, AC OFF, Charge Battery, Discharge Battery).
    *   Integrates with the FastAPI backend via the custom react hook `useSimulation.js`.

---

## Deployment Architectures

The project is fully ready for deployment. Since it consists of a Python FastAPI backend and a static React frontend, we have two primary deployment pathways:

### Option A: Serverless PaaS (Recommended & Simplest)
1.  **Frontend (Static Hosting)**:
    *   Host the built frontend assets (under `frontend/dist/`) on **Vercel**, **Netlify**, or **Cloudflare Pages**.
    *   Set the `VITE_API_BASE` environment variable to point to your deployed backend API URL.
2.  **Backend (Python App Hosting)**:
    *   Deploy the backend service to **Render** or **Railway**.
    *   The platform automatically detects the `requirements.txt` and starts the application via `uvicorn backend.api.main:app`.

### Option B: Docker Containerization (Using docker-compose)
We have added standard Dockerfiles under `docker/` to containerize the services:
1.  **Backend**: Packaged with a slim Python runtime. Running `docker/backend.Dockerfile` installs requirements and hosts the FastAPI server.
2.  **Frontend**: Uses a multi-stage build (`docker/frontend.Dockerfile`) that installs dependencies, builds static files using Node.js, and serves them with a lightweight Nginx web server.
3.  **Orchestration**: A `docker-compose.yml` is provided at the root. Running `docker-compose up --build` spins up both services locally or on any cloud Virtual Machine (e.g., AWS EC2, DigitalOcean Droplet, GCP Compute Engine).
