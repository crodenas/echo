# ECHO - Campaign Management API

ECHO is an enterprise software system designed to help teams manage and verify resource inventory data through automated notification cycles. The system enables teams to maintain data accuracy by sending periodic verification requests to resource contacts without requiring changes to existing data sources.

## Features

- **FastAPI-based REST API** for campaign management
- **Automated scheduling** using APScheduler for periodic verification campaigns
- **Multi-tenant support** for multiple teams and campaigns
- **Database integration** with SQLAlchemy
- **Read-only data source integration** preserving data ownership
- **Notification orchestration** as a service

## Developer Environment Setup

### Prerequisites

- **Python 3.13+** (required)
- **uv** package manager (recommended) or pip
- **Git** for version control

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd echo
   ```

2. **Set up the development environment using uv (recommended)**

   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Sync dependencies and create virtual environment
   uv sync
   ```

   **Alternative: Using pip and venv**

   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate

   # Install dependencies
   pip install -e .
   ```

3. **Verify installation**

   ```bash
   # With uv
   uv run python --version

   # With pip/venv
   python --version
   ```

### Project Structure

```text
echo/
├── src/                        # Application source code
│   ├── main.py                # FastAPI application entry point
│   ├── api/                   # HTTP routes and endpoints
│   │   └── routes/           # API route handlers
│   ├── services/              # Business logic layer (NEW)
│   │   └── campaign_service.py
│   ├── core/                  # Domain models and utilities
│   │   ├── models.py         # Pydantic domain models
│   │   ├── scheduler.py      # AWS EventBridge integration
│   │   └── config.py         # Configuration
│   ├── db/                    # Database layer
│   │   ├── schemas.py        # SQLAlchemy models
│   │   └── db_engine.py      # Database configuration
│   ├── templates/             # Jinja2 HTML templates
│   └── utils/                 # Utility modules
├── tests/                      # Test suite (NEW)
├── examples/                   # Sample data and configs (NEW)
├── scripts/                    # Utility scripts (NEW)
├── docs/                       # Documentation
│   ├── project_structure.md   # Architecture guide (NEW)
│   └── MIGRATION.md          # Migration guide (NEW)
├── QUICK_REFERENCE.md         # Quick reference guide (NEW)
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

**📚 See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for quick start guide**
**📖 See [docs/project_structure.md](docs/project_structure.md) for detailed architecture**
├── docs/                  # Documentation
├── utils/                 # Utility scripts and examples
└── examples/              # Usage examples
```

## Running the Application

### 1. FastAPI Development Server (Recommended for Development)

Start the FastAPI application with auto-reload for development:

```bash
# Using uv
uv run fastapi dev src/main.py

# Using pip/venv (after activation)
fastapi dev src/main.py
```

The API will be available at:

- **API Base URL**: <http://localhost:8000>
- **Interactive API Docs**: <http://localhost:8000/docs>
- **Alternative API Docs**: <http://localhost:8000/redoc>

### 2. FastAPI Production Server

For production deployment:

```bash
# Using uv
uv run fastapi run src/main.py

# Using pip/venv (after activation)
fastapi run src/main.py
```

### 3. Standalone Scheduler Mode

Run only the scheduler service without the web API:

```bash
# Using uv
uv run python src/main.py

# Using pip/venv (after activation)
python src/main.py
```

This mode runs the background schedulers directly and is useful for:

- Running scheduled campaigns without the web interface
- Background processing in containerized environments
- Testing scheduler functionality

### 4. Custom Python Scripts

You can also run individual components or examples:

```bash
# Run scheduler examples
uv run python utils/examples/background_scheduler.py
uv run python utils/examples/blocking_scheduler.py

# Run SQLAlchemy examples
uv run python utils/examples/sqlalchemy_example.py

# Generate sample data
uv run python utils/generate_sample_objects.py
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_campaigns.py
```

### Code Formatting and Linting

```bash
# Format code with black
uv run black src/

# Sort imports with isort
uv run isort src/

# Run linting with flake8
uv run flake8 src/
```

### Database Operations

The application uses SQLAlchemy with SQLite by default. The database file is located at `src/data/echo.db`.

To reset or initialize the database:

```bash
# Remove existing database
rm src/data/echo.db

# Run the application to recreate tables
uv run python src/main.py
```

## API Usage

### Available Endpoints

- `GET /` - Health check endpoint
- `GET /health` - Detailed health status
- `GET /campaigns` - List all campaigns (if campaigns module is available)
- Additional endpoints available in the interactive docs at `/docs`

### Example API Calls

```bash
# Health check
curl http://localhost:8000/

# Get health status
curl http://localhost:8000/health

# View available campaigns
curl http://localhost:8000/campaigns
```

## Configuration

The application can be configured through:

1. **Environment Variables**

   ```bash
   export ECHO_DB_URL="sqlite:///./echo.db"
   export ECHO_LOG_LEVEL="INFO"
   ```

2. **Configuration Files** (if implemented)
   - Place configuration files in the appropriate directory

## Deployment

### Docker (if Dockerfile exists)

```bash
# Build the image
docker build -t echo-api .

# Run the container
docker run -p 8000:8000 echo-api
```

### Direct Deployment

```bash
# Install production dependencies
uv sync --only-group main

# Run with a production ASGI server
uv run gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## Documentation

Detailed documentation is available in the `docs/` directory:

- [Design Document](docs/Design.md) - System architecture and design principles
- [Basic Concepts](docs/basic_concepts.md) - Core concepts and terminology
- [Modes](docs/modes.md) - Different operational modes
- [Shared Responsibility Model](docs/shared_responsibility_model.md) - Team responsibilities

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port by adding `--port 8001` to the fastapi command
2. **Database errors**: Ensure the `src/data/` directory exists and is writable
3. **Import errors**: Verify all dependencies are installed with `uv sync`

### Getting Help

- Check the [documentation](docs/) for detailed information
- Review the [examples](utils/examples/) for usage patterns
- Open an issue for bugs or feature requests

## License

[Add your license information here]
