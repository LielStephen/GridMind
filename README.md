# GridMind

Reinforcement learning powered smart energy management simulator. An RL agent learns to control HVAC and battery storage to minimise electricity cost while maintaining occupant comfort across a 24-hour building simulation.

## Architecture

```
GridMind/
├── backend/
│   ├── api/            # FastAPI server — REST endpoints for the dashboard
│   ├── config/         # Centralised configuration (dataclasses, no magic numbers)
│   ├── rl/             # Gymnasium environment (GridMind/Energy-v0)
│   ├── simulator/      # Physical models — HVAC, Battery, Weather, Pricing
│   ├── training/       # PPO training script (Stable-Baselines3)
│   ├── models/         # Saved model checkpoints (.zip)
│   └── utils/          # Shared helpers — obs parsing, formatting
│
├── frontend/           # React + Vite dashboard with Recharts visualisation
│
├── tests/              # pytest suite — env, models, helpers, API
│
├── datasets/           # Environment layouts and transition logs
├── docs/               # Technical documentation
├── docker/             # Containerisation configs
│
├── requirements.txt    # Python dependencies
├── start.ps1           # One-click launcher (backend + frontend)
└── .gitignore
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### Setup

```bash
# Clone and enter
cd GridMind

# Backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### Run

```powershell
# One-click (Windows)
.\start.ps1
```

Or manually in two terminals:

```bash
# Terminal 1 — Backend API
python -m uvicorn backend.api.main:app --reload --port 8000

# Terminal 2 — Frontend dev server
cd frontend && npm run dev
```

- **Dashboard**: http://localhost:5173
- **API docs**: http://localhost:8000/docs

## Environment

The Gymnasium environment (`GridMind/Energy-v0`) simulates a single building over a 24-hour period in 15-minute steps (96 steps per episode).

### Observation Space (7-dim)

| Index | Feature        | Range    |
|-------|----------------|----------|
| 0     | Hour of day    | 0 – 23   |
| 1     | Indoor temp    | 10 – 35  |
| 2     | Outdoor temp   | 0 – 45   |
| 3     | Solar gen (pu) | 0 – 1    |
| 4     | Battery SOC    | 0 – 1    |
| 5     | Grid price     | 0 – 1    |
| 6     | Occupancy      | 0 – 1    |

### Action Space (Discrete 5)

| Action | Effect              |
|--------|---------------------|
| 0      | Idle (do nothing)   |
| 1      | Turn AC on          |
| 2      | Turn AC off         |
| 3      | Charge battery      |
| 4      | Discharge battery   |

### Reward

Negative of `(energy_cost + comfort_penalty)`. The agent is penalised for grid consumption during peak pricing and for letting indoor temperature drift outside the 20–24 °C comfort band during occupied hours.

## Training

```bash
# Default: 50,000 timesteps
python -m backend.training.train

# Custom
python -m backend.training.train --timesteps 100000 --envs 4
```

TensorBoard logs are written to `./ppo_gridmind_tensorboard/`.

## Testing

```bash
python -m pytest tests/ -v
```

## API Endpoints

| Method | Path                | Description                          |
|--------|---------------------|--------------------------------------|
| GET    | `/`                 | Health check                         |
| GET    | `/simulation/state` | Current observation (no step)        |
| POST   | `/simulation/reset` | Reset to new episode                 |
| POST   | `/simulation/step`  | Advance one step (query: `action`)   |

## License

MIT
