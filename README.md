# 🧠 NeuralSpace – Cognitive Security Universe

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/neuralspace-ai.svg)](https://badge.fury.io/py/neuralspace-ai)
[![CI/CD](https://github.com/krishnakanthsharmat-cloud/NeuralSpace/actions/workflows/neuralspace-scan.yml/badge.svg)](https://github.com/krishnakanthsharmat-cloud/NeuralSpace/actions)

**NeuralSpace** is the world's first **self-organizing, zero-trust security universe** for code. It doesn't just scan for known threats—it builds a living, evolving topology of your codebase where every branch has its own specialized "neural brain." 

It combines a **Covalent Tree** (self-evolving topology), a **Hive Mind** (emergent intelligence), a **Zero-Trust Mesh** (cryptographic trust), and **AST/CFG Taint Analysis** (real data-flow tracking) into a single, ultra-lightweight (~8 KB) system.

---

## 🔥 The Problem We Solve

| Current Tool | Limitation | NeuralSpace Advantage |
| :--- | :--- | :--- |
| **Traditional AV** | Relies on known signatures. | Blocks zero‑day obfuscated threats. |
| **SAST (SonarQube)** | 99.5% false positives. | Contextual detection + Taint Analysis (e.g., `requests.get` alone is safe; `requests.get + exec` is a threat). |
| **Transformer Models** | Huge, slow, cloud‑dependent. | Lightweight (~8 KB), runs instantly on CPU. |
| **File Watchers** | React to files, don't understand content. | Routes files dynamically into a living knowledge tree (the Covalent Tree). |

---

## ✨ Key Features

- **🧬 Self‑Evolving Topology (The Covalent Tree)** – The tree spawns new branches *anticipatorily* when it detects structural drift (drift velocity > 0.5). It doesn't just classify code; it *organizes* your codebase into a living taxonomy.
- **🧠 Distributed Neural Atoms** – Each tree branch has its own `PureNeuralAtom` (512→4→4 network) initialized with a unique seed. This creates specialized "brains" for different code families.
- **🤝 Hive Mind (Emergent Intelligence)** – Multiple agents communicate and form a consensus on threats. The collective intelligence (consensus ≥ 0.7) can override individual node decisions.
- **🛡️ Zero-Trust Security Mesh** – All threat reports are cryptographically signed with RSA. Nodes earn trust over time; low-trust nodes (score < 0.3) are ignored.
- **🔍 AST/CFG Taint Analysis** – Tracks whether tainted data (user input, network data) reaches dangerous sinks (`exec`, `eval`, `os.system`). Real data-flow analysis, not just token matching.
- **🌍 Polyglot** – Scans **Python, JavaScript, TypeScript, Go, and Rust** (with Tree-Sitter AST parsing).
- **⚡ Ultra‑Lightweight & Local** – Trains in under 60 seconds on a standard CPU. No cloud. No GPU. (~8 KB model).
- **🤖 GitHub App Integration** – Auto‑scans Pull Requests and posts comments with detailed decision traces.
- **🌐 Federated Intelligence** – Global aggregator shares anonymized threat signatures across instances, creating a living immune system.
- **🗣️ God User Interface** – Natural language commands to shape the universe (`health`, `spawn branch`, `show threats`, `evolve`).

---

## 🏗️ How It Works

1. **Tokenization + Taint Analysis** – Code is parsed via Tree-Sitter AST, and data-flow taint analysis tracks user input to dangerous sinks.
2. **Routing** – The vector descends the Covalent Tree. If it matches a child node (cosine similarity > 0.85), it dives deeper. Otherwise, it stops.
3. **Hive Mind Consensus** – All active nodes vote on the threat. The collective decision overrides individual errors.
4. **Judgment** – The terminal node's `PureNeuralAtom` computes two scores:
   - **Sentinel (S)** – Threat probability (class 3).
   - **Logic (L)** – Safe probability (class 0).
5. **Enforcement** – If `S > 0.25` or `L < 0.2`, the file is quarantined and cryptographically reported.
6. **Evolution** – If the file is allowed but deviates significantly (drift velocity > 0.5), the tree **anticipatorily fractures** and spawns a new child node.

---

## 🚀 Quick Start (Global Install)

### Installation (One Command)

```bash
pip install neuralspace-ai

## Basic Usage

```bash

###  Scan a project folder
neuralspace scan ./your_project --quarantine rename

### Watch a folder in real-time
neuralspace watch ./your_project

###  Sync with the global threat intelligence network
neuralspace sync

### Advanced: Train the AI (Optional)
### The package comes pre-trained. But you can retrain it on your own dataset:

```bash
neuralspace generate
neuralspace train