# 🎟️ SMAREET — Smart Decentralized Event Ticketing

> A next-generation decentralized event ticketing platform built on the **Algorand blockchain** using **AlgoKit**. SMAREET eliminates ticket fraud, prevents scalping through on-chain resale price caps, and provides full transparency for event organizers and attendees.

---

## 📋 Problem Statement

Ticket fraud and predatory resale pricing are massive problems in the live events industry. Counterfeit tickets, inflated resale prices (often 3–10x face value), and lack of transparency cost consumers billions annually. Centralized ticketing platforms take hefty fees while offering no real protection against scalping.

**SMAREET** solves this by:
- **Minting every ticket as a unique NFT (ASA)** on Algorand — making counterfeiting impossible
- **Enforcing on-chain resale price caps** — the smart contract rejects any transfer above the max resale price
- **Providing full provenance tracking** — every mint, transfer, and ownership change is recorded on-chain
- **Near-zero transaction fees** — Algorand's ~0.001 ALGO fees make microtransactions viable

---

## 🌐 Live Demo

🔗 **Live URL**: [https://smareet.vercel.app](https://smareet.vercel.app)

---

## 🎬 Demo Video

📹 **LinkedIn Demo Video**: _[Link to be added after recording]_  
_(2–3 min walkthrough tagging [@RIFT](https://www.linkedin.com/company/rift-pwioi/))_

---

## 🔗 Algorand Testnet Deployment

| Item | Value |
|------|-------|
| **App ID (Testnet)** | `755791847` |
| **Lora Explorer** | [View on Lora](https://lora.algokit.io/testnet/application/755791847) |
| **Pera Explorer** | [View on Pera](https://testnet.explorer.perawallet.app/application/755791847/) |
| **Network** | Algorand Testnet |

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    SMAREET Frontend                       │
│          React + Vite + Framer Motion                    │
│   Wallet: Pera / Defly / Exodus / Lute                   │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │Send ALGO │ │Mint NFT  │ │Create ASA│ │ My Tickets │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘  │
│       │             │            │              │         │
└───────┼─────────────┼────────────┼──────────────┼────────┘
        │             │            │              │
        ▼             ▼            ▼              ▼
┌──────────────────────────────────────────────────────────┐
│              Algorand Testnet (AlgoNode)                  │
│                                                          │
│  ┌──────────────────────────────────────┐                │
│  │   EventTicketing Smart Contract      │                │
│  │   App ID: 755791847                  │                │
│  │                                      │                │
│  │   mint_ticket(price, seat) → ASA     │                │
│  │   transfer_ticket(payment, asset)    │                │
│  │   ✓ Resale price cap enforcement     │                │
│  │   ✓ Inner transactions (ASA create)  │                │
│  └──────────────────────────────────────┘                │
│                                                          │
└──────────────────────────────────────────────────────────┘
        ▲
        │  Chain Subscriber (real-time sync)
        ▼
┌──────────────────────────────────────────────────────────┐
│              FastAPI Backend                              │
│                                                          │
│  POST /api/tickets/mint   → On-chain mint + DB store     │
│  GET  /api/tickets        → List / filter tickets        │
│  POST /api/events         → Create events                │
│  GET  /api/transfers      → Transfer history             │
│  GET  /api/chain/app-info → Live contract state          │
│                                                          │
│  SQLite DB  ←→  Chain Subscriber (background sync)       │
└──────────────────────────────────────────────────────────┘
```

**Key interaction flow:**
1. User connects an Algorand wallet (Pera/Defly) on the frontend
2. User mints a ticket → frontend calls backend `/api/tickets/mint`
3. Backend invokes the `EventTicketing` smart contract's `mint_ticket` ABI method
4. Smart contract creates a unique ASA (NFT) via inner transaction on Testnet
5. ASA ID and ownership are stored both on-chain and in the backend database
6. Chain subscriber continuously syncs on-chain state to keep the database up-to-date
7. Resale transfers are enforced by the smart contract — price cannot exceed `max_resale_price`

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Blockchain** | Algorand Testnet |
| **Dev Toolkit** | AlgoKit v2+ (scaffold, build, deploy) |
| **Smart Contract** | algopy (Algorand Python) — ARC4 standard |
| **Contract Artifacts** | ARC-56 app spec, auto-generated TypeScript client |
| **Frontend** | React 18 + TypeScript + Vite |
| **UI/Animation** | Framer Motion, DaisyUI, Custom CSS |
| **Wallet Integration** | `@txnlab/use-wallet-react` (Pera, Defly, Exodus, Lute) |
| **Backend** | Python FastAPI + SQLAlchemy (async) |
| **Database** | SQLite (via aiosqlite) |
| **Chain Sync** | Custom chain subscriber (real-time Indexer polling) |
| **Hosting** | Vercel (frontend) |
| **IPFS** | Pinata (NFT media/metadata uploads) |

---

## ⚙️ Installation & Setup

### Prerequisites

- **Node.js** 20+ and **npm** 9+
- **Python** 3.12+
- **AlgoKit** CLI — [Install Guide](https://developer.algorand.org/algokit/)
- An Algorand Testnet wallet funded via [Testnet Dispenser](https://bank.testnet.algorand.network/)

### 1. Clone the repository

```bash
git clone https://github.com/SKYGOD07/RIFT-26.git
cd RIFT-26
```

### 2. Bootstrap the AlgoKit workspace

```bash
algokit project bootstrap all
```

### 3. Build smart contracts

```bash
cd projects/contracts
poetry install
algokit project run build
```

### 4. Deploy to Testnet (if redeploying)

```bash
# Copy and fill in your mnemonic
cp .env.template .env
# Edit .env → set DEPLOYER_MNEMONIC

python -m smart_contracts.ticketing.deploy_testnet
```

The deploy script will output your **App ID** and save it to `.env`.

### 5. Start the backend

```bash
cd ../../backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt  # or: poetry install
python -m app.main
```

Backend runs at `http://localhost:8000` with Swagger docs at `/docs`.

### 6. Start the frontend

```bash
cd ../projects/frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### 7. Environment Variables (Frontend)

Create `projects/frontend/.env`:

```bash
VITE_ALGOD_SERVER=https://testnet-api.algonode.cloud
VITE_ALGOD_PORT=
VITE_ALGOD_TOKEN=
VITE_ALGOD_NETWORK=testnet
VITE_INDEXER_SERVER=https://testnet-idx.algonode.cloud
VITE_INDEXER_PORT=
VITE_INDEXER_TOKEN=
VITE_PINATA_JWT=<your-pinata-jwt>
```

---

## 📖 Usage Guide

### Connect Wallet
Click **"Connect Wallet"** in the navbar → select Pera or Defly → authorize the connection.

### Send ALGO
Open the **Send Algo** feature → enter a recipient address → confirm the transaction in your wallet.

### Mint NFT (ARC-18)
Open **Mint NFT** → upload an image → enter name and description → the media is pinned to IPFS via Pinata → an ARC-18 NFT is minted on Algorand Testnet.

### Create Token (ASA)
Open **Create Token** → fill in token name, unit, decimals, and supply → a new Algorand Standard Asset is created on Testnet.

### Asset Opt-In
Open **Asset Opt-In** → enter the ASA ID of the asset you want to receive → sign the opt-in transaction.

### Counter Contract
Open **Counter Contract** → interact with the on-chain counter (App ID 747652603) → increment/read state to see contract interaction.

### Decentralized Bank
Open **Decentralized Bank** → deposit or withdraw ALGOs from the bank smart contract → view on-chain transaction history.

### My Tickets
Open **My Tickets** → view all ticket NFTs owned by your wallet → see seat numbers and ticket details.

---

## ⚠️ Known Limitations

- **Testnet only** — the smart contract is deployed to Algorand Testnet, not MainNet
- **Backend not hosted** — the FastAPI backend currently runs locally; a hosted version would be needed for full production use
- **Single-event contract** — the current `EventTicketing` contract stores one `max_resale_price` globally; a production version should support per-event pricing
- **No secondary market UI** — while the smart contract supports `transfer_ticket` with price enforcement, the frontend doesn't yet have a marketplace/resale interface
- **Pinata dependency** — NFT minting requires a valid Pinata JWT for IPFS uploads
- **No mobile app** — the platform is web-only; a mobile wallet-native experience would improve accessibility

---

## 👥 Team Members

| Name | Role |
|------|------|
| **[Your Name]** | Full-Stack Developer / Smart Contract Engineer |
| **[Team Member 2]** | _[Role]_ |
| **[Team Member 3]** | _[Role]_ |

> ⚠️ **Update this section with your actual team members before submission.**

---

## 📚 References

- [Algorand Developer Portal](https://dev.algorand.co/)
- [AlgoKit Documentation](https://developer.algorand.org/algokit/)
- [AlgoKit Workshops](https://algorand.co/algokit-workshops)
- [Algodevs YouTube](https://www.youtube.com/@algodevs)

---

## 📄 License

This project was built for the **RIFT 2026 Hackathon — Algorand Open Innovation Track**.

---

_Built with ❤️ on Algorand — SMAREET © 2026_
