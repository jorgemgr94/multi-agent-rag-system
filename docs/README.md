# Multi-Agent RAG System

A **production-oriented multi-agent AI system** designed for knowledge-driven automation, decision support, and consulting-grade workflows.

## Overview

This system implements:

- 🤖 **Multi-agent orchestration** — Specialized agents with clear responsibilities
- 🔍 **Retrieval-Augmented Generation (RAG)** — Context-aware responses from knowledge bases
- 🧠 **Vector databases & semantic memory** — FAISS (local) and Pinecone (managed)
- ⚡ **Automation pipelines** — Integration with external APIs
- 📊 **Observability & cost control** — Token tracking, latency metrics

## Architecture

```mermaid
flowchart TD
    subgraph Client
        A[POST /tasks]
    end

    subgraph Orchestrator
        B[Task Input] --> C[PlannerAgent]
        C -->|decompose| D[RetrieverAgent]
        D -->|fetch context| E[ExecutorAgent]
        E -->|execute actions| F[ValidatorAgent]
        F -->|validate| G{Success?}
        G -->|yes| H[Final Response]
        G -->|no| C
    end

    subgraph Knowledge["Knowledge Layer"]
        D --> I[(Vector Store)]
        I --> D
    end

    subgraph Memory["Memory Layer"]
        J[(Long-term Memory)]
        K[(Episodic Memory)]
    end

    A --> B
    H --> L[Response]

    style I fill:#f9f,stroke:#333
    style J fill:#90EE90,stroke:#2d5a2d,color:#1a1a1a
    style K fill:#90EE90,stroke:#2d5a2d,color:#1a1a1a
    style Memory fill:#e8f5e9,stroke:#4a7c59
```

### Agents

| Agent | Responsibility |
|-------|----------------|
| **PlannerAgent** | Decomposes tasks, defines execution strategy |
| **RetrieverAgent** | Fetches relevant knowledge via semantic search |
| **ExecutorAgent** | Executes automation actions and API calls |
| **ValidatorAgent** | Validates outputs, detects failures |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/multi-agent-rag-system.git
cd multi-agent-rag-system

# Install dependencies
make install-dev

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run tests
make test

# Start development server
make dev
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness check |
| `/status` | GET | Agent configuration and status |
| `/tasks` | POST | Process a task through the multi-agent system |

### Example Request

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"task": "Find relevant documentation about our refund policy and draft a response"}'
```

## Development

### Commands

```bash
make dev          # Start dev server with hot reload
make test         # Run tests
make install-dev  # Install with dev dependencies
make docker-build # Build Docker image
make docker-up    # Run with docker-compose
make clean        # Clean cache files
```

## Design Philosophy

- **Agents have explicit and limited responsibilities**
- **Retrieval is intentional**, not automatic
- **Memory is selective and scoped**, not infinite
- **Automation is observable and auditable**
- **Costs, latency, and failure modes are first-class concerns**
- **Every architectural decision is explainable**
