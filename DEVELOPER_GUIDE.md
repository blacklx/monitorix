# Developer Guide

This guide is for developers who want to contribute to Monitorix or set up a development environment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Backend Development](#backend-development)
- [Frontend Development](#frontend-development)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [Code Style](#code-style)
- [Contributing](#contributing)

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker and Docker Compose (optional, for containerized development)
- Git

## Development Setup

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/monitorix.git
cd monitorix
```

2. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the `backend` directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/monitorix
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the `frontend` directory:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port Vite assigns).

## Project Structure

```
monitorix/
├── backend/
│   ├── alembic/          # Database migrations
│   ├── routers/          # API route handlers
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── database.py       # Database connection
│   ├── auth.py           # Authentication utilities
│   ├── main.py           # FastAPI application
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── contexts/     # React contexts
│   │   ├── hooks/        # Custom hooks
│   │   ├── utils/        # Utility functions
│   │   └── i18n/         # Internationalization
│   └── package.json      # Node dependencies
├── docker-compose.yml    # Docker Compose configuration
└── README.md             # Project README
```

## Backend Development

### API Structure

The backend uses FastAPI with the following structure:

- **Routers**: Located in `backend/routers/`, each router handles a specific domain (auth, nodes, vms, services, etc.)
- **Models**: SQLAlchemy ORM models in `backend/models.py`
- **Schemas**: Pydantic schemas for request/response validation in `backend/schemas.py`
- **Middleware**: Custom middleware in `backend/middleware/`

### Adding a New Endpoint

1. Create or update the appropriate router in `backend/routers/`
2. Add the route handler function
3. Define request/response schemas in `backend/schemas.py`
4. Register the router in `backend/main.py`
5. Add tests in `backend/tests/`

Example:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_active_user

router = APIRouter(prefix="/api/example", tags=["example"])

@router.get("/")
async def get_example(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    return {"message": "Hello, World!"}
```

### Database Models

Models are defined using SQLAlchemy in `backend/models.py`. When adding a new model:

1. Define the model class inheriting from `Base`
2. Create an Alembic migration: `alembic revision -m "add_example_model"`
3. Update the migration file with the schema changes
4. Run the migration: `alembic upgrade head`

## Frontend Development

### Component Structure

- **Pages**: Full page components in `frontend/src/pages/`
- **Components**: Reusable components in `frontend/src/components/`
- **Hooks**: Custom React hooks in `frontend/src/hooks/`
- **Utils**: Utility functions in `frontend/src/utils/`

### Adding a New Page

1. Create a new component in `frontend/src/pages/`
2. Add the route in `frontend/src/App.jsx`
3. Add navigation link in `frontend/src/components/Layout.jsx`
4. Add translations in `frontend/src/i18n/locales/`

### State Management

The frontend uses React Context API for state management:
- `AuthContext`: Authentication state
- Additional contexts can be added as needed

### Internationalization

All user-facing strings should be translated. Add translations to:
- `frontend/src/i18n/locales/en.json` (English, base)
- `frontend/src/i18n/locales/no.json` (Norwegian)
- `frontend/src/i18n/locales/sv.json` (Swedish)
- And other language files

## Database Migrations

Migrations are managed using Alembic:

```bash
# Create a new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Testing

### Backend Tests

Backend tests use pytest:

```bash
cd backend
pytest tests/ -v
```

### Frontend Tests

Frontend tests (when implemented) will use Vitest or similar:

```bash
cd frontend
npm test
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use Black for formatting (when configured)

### JavaScript/React

- Follow ESLint rules
- Use functional components with hooks
- Use meaningful variable and function names
- Maximum line length: 100 characters

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes: `git commit -m "Add feature: description"`
7. Push to your branch: `git push origin feature/your-feature`
8. Create a Pull Request

### Commit Messages

Use clear, descriptive commit messages:
- `Add: Feature description`
- `Fix: Bug description`
- `Update: Change description`
- `Refactor: Refactoring description`

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

