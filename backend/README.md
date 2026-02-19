# EventTicketing Backend

FastAPI backend for the EventTicketing dApp on Algorand.

## Quick Start

```bash
cd backend

# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows

# 2. Install dependencies  
pip install -e ".[dev]"
# Or with poetry:
poetry install

# 3. Copy and fill .env
copy .env.template .env
# Edit .env → set DEPLOYER_MNEMONIC and APP_ID

# 4. Run the server
python -m app.main
# Or:
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + App ID |
| POST | `/api/events` | Create event |
| GET | `/api/events` | List events |
| **POST** | **`/api/tickets/mint`** | **Mint ticket on-chain + save to DB** |
| GET | `/api/tickets` | List tickets |
| GET | `/api/tickets/asa/{asa_id}` | Get ticket by ASA ID |
| POST | `/api/users` | Register user by wallet |
| GET | `/api/transfers` | Transfer history |
| GET | `/api/chain/app-info` | Query contract state on-chain |

## Architecture

```
POST /api/tickets/mint
  → AlgorandService.mint_ticket_on_chain()
    → EventTicketingClient.send.mint_ticket()  (typed client)
      → Algorand Testnet (creates ASA)
  → Save to SQLite/Postgres

Background: ChainSubscriber
  → Polls Algorand Indexer every 5s
  → Detects mint_ticket / transfer_ticket ABI calls
  → Syncs to database
```

## Swagger Docs

Once running, open: `http://localhost:8000/docs`
