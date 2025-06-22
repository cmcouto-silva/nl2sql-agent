# NL2SQL Agent

> 🎯 **Featured at SciPy Conference 2025:**  
> [Building an AI Agent for Natural Language to SQL Query Execution on Live Databases](https://cfp.scipy.org/scipy2025/talk/XUYKZZ/)  
> 📅 **July 8, 2025** | 📍 **Tacoma, WA** | ⏱️ **4-hour hands-on tutorial**

This project implements a session-based, RAG-powered AI agent that translates natural language into SQL queries for live querying of PostgreSQL databases. It leverages LangChain, LangGraph, PGVector, and modern agentic patterns with production-quality tooling.

## ✨ Key Features

By the end of the tutorial, you'll have **a fully working solution you can adapt to your own datasets**:

✅ **LangGraph Orchestration**: Using the latest API references for robust agent workflows  
✅ **Smart Routing**: Intelligent switching between SQL and ReAct-style chat agents  
✅ **RAG with PGVector**: Retrieve few-shot SQL examples based on user queries  
✅ **Comprehensive Guardrails**: Validation and human-in-the-loop approval  
✅ **Session Memory**: Token/cost tracking with LangSmith integration  
✅ **End-to-End Flow**: From schema ingestion to query execution on live databases  
✅ **Production Ready**: Built with modern Python tooling and real-world considerations

## 🏗️ Architecture

![Agent Flow Diagram](./artifacts/agent-flow.png)

The system intelligently routes user queries through specialized agents:
- **SQL Agent**: Handles database queries with RAG context retrieval
- **Chat ReAct Agent**: Manages conversational interactions with custom tools

## 🛠️ Tech Stack

| Layer         | Tools & Libraries                           |
|---------------|---------------------------------------------|
| AI / Agents   | `LangGraph`, `LangChain`, `OpenAI`          |
| Retrieval     | `PGVector`, SQL context + query embeddings  |
| Database      | `PostgreSQL`, `SQLAlchemy`, `psycopg`       |
| Dev Tooling   | `uv`, `Ruff`, Python 3.12+                  |
| Monitoring    | `LangSmith`                                 |
| Deployment    | `FastAPI`, `Docker`                         |

## 🚀 Quick Start

### Prerequisites

Before getting started, you'll need to install the required tools and dependencies.  
See the [prerequisites](docs/prerequisites.md) for detailed installation instructions.

**Required:**
- [Git](https://git-scm.com/) for cloning the repository and switching between branches
- [UV](https://docs.astral.sh/uv/getting-started/installation/) for Python project management
- PostgreSQL client libraries to query the database
- [Docker](https://www.docker.com/) *(optional)* for containerized deployment
- A Python IDE of your choice (e.g., VS Code)


### Installation

```bash
# Clone the repository
git clone https://github.com/cmcouto-silva/nl2sql-agent.git
cd nl2sql-agent

# Install dependencies with UV
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database credentials
```

> Further instructions to be provided.

## 📚 Documentation

- Setup Guide - *Coming soon*
- Tutorial Guide - *Coming soon*
- Deployment Guide - *Coming soon*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- SciPy 2025 Conference
- Olist Brazilian E-Commerce dataset contributors
- Global Land Use and Environmental Lab (GLUE) at UW-Madison
