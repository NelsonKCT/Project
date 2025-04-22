# 🔐 Private Set Intersection (PSI) System

A full-stack implementation of a **privacy-preserving data exchange system** using blockchain principles, IPFS for decentralized storage, and Private Set Intersection (PSI) cryptography for secure record comparison — without revealing private data.

---

## 📘 Project Overview

This project enables two clients to securely identify overlapping records in their datasets without exposing non-overlapping entries. The server coordinates interaction, but never sees the data.

**Core Features:**
- 🔏 Blind hashing & deterministic prime generation
- 🔁 4-step PSI protocol implementation
- 🧾 Encrypted Excel dataset handling
- 🗂 IPFS for decentralized file storage
- 🧠 Fully local record matching with SQLite support

---

## 🧠 Architecture

```
Client A <-> IPFS <-> Server <-> Client B
```

- IPFS is used as a shared encrypted data bus
- Server acts as a secure coordinator
- PSI Protocol protects data privacy through blinding and hashing

---

## 🗂 Directory Structure

```
blockchaingroupproject-project.git/
├── ClientA/                  # PSI client (party A)
│   ├── Client.py             # Client socket logic and PSI protocol handler
│   ├── id_database.py        # Local SQLite manager for CIDs
│   ├── id_record.db          # Local CID record database
│   ├── Message.py            # JSON message utilities
│   ├── psi_dh.py             # PSI logic using modular exponentiation
│   ├── Request.py            # Request DB management
│   ├── upload_to_ipfs.py     # File upload handler to IPFS
│   ├── RequestsDataBase/
│   │   └── Request.db        # Merge request records
│   └── Test_Data/            # Test datasets (Excel)
│       ├── demo1.xlsx
│       └── test_data_1.xlsx
├── ClientB/                  # PSI client (party B), mirror of ClientA
│   └── ...                   # Identical structure and logic
└── Server/                   # Central coordinator
    ├── DataBase.py           # Server-side database utility
    ├── HandleClient.py       # Client session handler
    ├── main.py               # Entry point for server launch
    ├── MergeRequest.py       # Merge logic handler
    ├── Message.py            # Server-side message processing
    ├── Server.py             # Core server implementation
    ├── SQLData.py            # Server-side SQL abstraction
    ├── UserInterFace.py      # CLI interface
    ├── UserSession.py        # Session management
    ├── Verify Merge Request Columns.py
    ├── MergeRequestDataBase/
    │   └── mergeRequest.db
    └── UserDataBase/
        └── users.db
```

---

## ⚙️ How It Works

1. **Step 1 (Blinding):** Each client blinds hashes of their identifier columns.
2. **Step 2 (Double-Blinding):** Clients download and blind partner values.
3. **Step 3 (Intersection):** Double-blinded values are intersected.
4. **Step 4 (Merge):** Intersected records are extracted and securely merged.

Each step is modular and executed based on server-coordinated signals.

---

## 🔧 Tech Stack

- **Python 3.10**
- **SQLite3** for local/remote database
- **IPFS** (go-ipfs) for decentralized file storage
- **Pandas**, **SymPy**, **Hashlib** for data & crypto logic

---

## 🛡 Security Features

- Uses **modular exponentiation** for cryptographic blinding
- Ensures **data remains private** at all steps
- No raw data transmission — only hashed or blinded data
- Deterministic primes eliminate the need for shared secrets