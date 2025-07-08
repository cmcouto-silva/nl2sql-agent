# NL2SQL Agent API

This API provides endpoints for the NL2SQL agent that translates natural language into SQL queries and executes them safely.

## Quick Start

### 1. Start the API Server

```bash
# From the project root
python -m nl2sql.api.main
```

The API will be available at `http://localhost:8000`

### 2. Test with Terminal Chat

```bash
# Run the terminal chat interface
python scripts/terminal_chat.py
```

### 3. API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Endpoints

### Health Check
- **GET** `/health`
- Returns the health status and database connectivity

### Chat
- **POST** `/chat/`
- Send natural language queries to the NL2SQL agent
- Request body:
  ```json
  {
    "message": "Show me the top 5 customers by total orders",
    "session_id": "optional-session-id"
  }
  ```

## Features

- **PostgreSQL Memory**: Maintains conversation context using PostgreSQL as the memory backend
- **Session Management**: Automatic session ID generation with timestamp format `test_YYYYMMDD_HHMMSS_<uuid>`
- **SQL Safety**: Validates SQL queries for safety before execution
- **Error Handling**: Comprehensive error handling with detailed messages
- **CORS Support**: Configured for web application integration

## Architecture

The API leverages the existing NL2SQL agent components:
- Database connector with `get_psycopg_connection()`
- Vector store for semantic search
- LangGraph agent workflow
- PostgreSQL memory for session persistence

## Session IDs

If no session ID is provided, the API automatically generates one with the format:
```
test_20250708_143022_a1b2c3d4
```

This allows for easy testing and session tracking. 