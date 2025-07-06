# 🛠️ Prerequisites

Before running this project locally, ensure the following tools are installed on your system.

## 1. Git

Required to clone the repository and switch between tutorial branches.

**Installation:**

- **Linux**: `sudo apt install git` (Ubuntu/Debian)
- **macOS**: `brew install git` or download from [git-scm.com](https://git-scm.com/downloads)
- **Windows**: Download from [git-scm.com](https://git-scm.com/downloads) or use `winget install Git.Git`

**Verify:** `git --version`

## 2. UV

We use [**UV**](https://github.com/astral-sh/uv) for fast Python environment and dependency management. UV automatically handles Python installation and virtual environments.

**Installation:**

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Verify:** `uv --version`

## 3. PostgreSQL Client

Required to connect to PostgreSQL databases.

**macOS:**

```bash
brew install postgresql
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt install postgresql-client
```

**Windows:**

- Download from [postgresql.org/download](https://www.postgresql.org/download/windows/)

**Verify:** `psql --version`

---

## 4. Docker (Optional)

Used for containerized deployment and running PostgreSQL locally during development.

**Installation:**

- **Linux**: Follow [official Docker installation guide](https://docs.docker.com/engine/install/)
- **macOS/Windows**: Download Docker Desktop from [docker.com](https://www.docker.com/get-started)

**Verify:** `docker --version`

---

## 5. Python IDE (Recommended)

Use any Python-compatible code editor:

- **[VS Code](https://code.visualstudio.com/)** - Popular, free, extensive Python support
- **[Cursor](https://www.cursor.com/)** - AI-native IDE based on VS Code (recommended for AI development)
- **[WindSurf](https://windsurf.com/)** - Another AI-native IDE based on VS Code (recommended for AI development)

## ✅ Quick Setup Verification

After installing the prerequisites, verify your setup:

```bash
# Check all tools
git --version
uv --version
psql --version
docker --version  # (optional)
```

---

## 🔧 Troubleshooting

**UV not found after installation:**

- Restart your terminal
- Check if UV is in your PATH: `echo $PATH` (Linux/macOS) or `$env:PATH` (Windows)

**PostgreSQL libraries not found:**

- Ensure development headers are installed (`libpq-dev` on Linux)
- On Windows, make sure PostgreSQL bin directory is in PATH

**Docker permission issues (Linux):**

```bash
sudo usermod -aG docker $USER
# Log out and back in
```

---

Ready to proceed? Return to the [README](../README.md#installation) for project setup!
