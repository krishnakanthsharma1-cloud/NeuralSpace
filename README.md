# 🧠 NeuralSpace – Cognitive Security Universe

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/neuralspace-ai.svg)](https://badge.fury.io/py/neuralspace-ai)
[![CI/CD](https://github.com/krishnakanthsharmat-cloud/NeuralSpace/actions/workflows/neuralspace-scan.yml/badge.svg)](https://github.com/krishnakanthsharmat-cloud/NeuralSpace/actions)

**NeuralSpace** is a self-organizing, zero‑trust security mesh for code. It combines a **Covalent Tree** (self‑evolving topology), a **Hive Mind** (emergent intelligence), **AST/CFG Data‑Flow Analysis**, and a **Zero‑Trust Security Mesh** (RSA 2048 signing) into a single ultra‑lightweight (~8 KB) system.

> 📌 **Version 4.1.0** — Ship pre‑trained weights, fixed `importlib`+`chr()` evasion, raised default threshold to `0.25`, added `--threshold` CLI flag.

---

## 🔥 The Problem We Solve

| Current Tool | Limitation | NeuralSpace Advantage |
| :--- | :--- | :--- |
| **Traditional AV** | Relies on known signatures. | Blocks zero‑day obfuscated threats. |
| **SAST (SonarQube)** | 99.5% false positives. | Contextual detection + Taint Analysis. |
| **Transformer Models** | Huge, slow, cloud‑dependent. | Lightweight (~8 KB), runs instantly on CPU. |
| **File Watchers** | React to files, don't understand content. | Routes files dynamically into a living knowledge tree. |

---

## ✨ Key Features (v4.1.0)

- **🧬 Self‑Evolving Topology** – The Covalent Tree spawns new branches *anticipatorily* when it detects structural drift (drift velocity > 0.5).
- **🌊 True Data‑Flow Analysis** – Tracks tainted input (`input()`, `sys.argv`) to dangerous sinks (`exec`, `eval`, `os.system`). Catches `importlib` + `chr()` evasions.
- **🔒 Zero‑Trust Security Mesh** – All threat reports are cryptographically signed with RSA 2048. Nodes maintain a public key registry (PKI) and earn trust over time.
- **🧠 Hive Mind (Emergent Intelligence)** – Multiple agents communicate and form a consensus on threats (consensus ≥ 0.7).
- **🛡️ Adversarial Robustness** – Trained on obfuscated variants (`getattr`, string‑concat, `__import__`, `chr()`).
- **🌍 Polyglot** – Scans **Python, JavaScript, TypeScript, Go, and Rust** (Tree‑Sitter AST parsing).
- **⚡ Ultra‑Lightweight & Local** – ~8 KB model, trains in <60 seconds on CPU.
- **🔧 CLI Configurable** – New `--threshold` flag to adjust sensitivity.
- **🤖 GitHub App Integration** – Auto‑scans Pull Requests and posts comments.

---

## 🏗️ How It Works

1. **Tokenization + Data‑Flow** – Code is parsed via Tree‑Sitter AST; data‑flow tracks tainted input to dangerous sinks.
2. **Routing** – The vector descends the Covalent Tree. If it matches a child node (cosine similarity > 0.85), it dives deeper.
3. **Hive Mind Consensus** – All active nodes vote on the threat. The collective decision overrides individual errors.
4. **Judgment** – The terminal node's `PureNeuralAtom` computes Sentinel (S) and Logic (L) scores.
5. **Enforcement** – If `S > threshold` (default 0.25) or `L < 0.2`, the file is quarantined and cryptographically reported.
6. **Evolution** – If the file is allowed but deviates significantly (drift velocity > 0.5), the tree **anticipatorily fractures** and spawns a new child node.

---

## 🚀 Quick Start

### Installation (One Command)

```bash
pip install neuralspace-ai