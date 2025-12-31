# Contributing to Monitorix

Thank you for considering contributing to Monitorix! This document provides guidelines on how you can contribute.

**GitHub Repository**: [https://github.com/blacklx/monitorix](https://github.com/blacklx/monitorix)

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Environment](#development-environment)
- [Code Standards](#code-standards)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)

## 📜 Code of Conduct

This project follows a code of conduct. By participating, you are expected to uphold this code.

### Our Standards

- Be respectful and inclusive
- Welcome constructive feedback
- Focus on what is best for the community
- Show empathy towards other members

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug:

1. Check [TODO.md](TODO.md) to see if the bug is already documented
2. If not, create a new issue with:
   - Description of the problem
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment information (OS, Docker version, etc.)
   - Logs or screenshots if relevant

### Suggesting Enhancements

1. Check [TODO.md](TODO.md) to see if the enhancement is already planned
2. Create an issue with:
   - Description of the enhancement
   - Why it's useful
   - Examples of usage

### Submitting Code

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🛠 Development Environment

### Setup

1. Clone the project:
```bash
git clone https://github.com/blacklx/monitorix.git
cd monitorix
```

2. Copy `.env.example` to `.env` and configure

3. Start development environment:
```bash
docker-compose up -d
```

### Backend Development

Backend runs with hot-reload:

```bash
# Backend will automatically restart on file changes
docker-compose logs -f backend
```

Test backend API:
```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

### Frontend Development

For local development without Docker:

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on `http://localhost:3000` with hot-reload.

### Database

Access database:

```bash
# PostgreSQL CLI
docker-compose exec postgres psql -U monitorix -d monitorix

# Or from host
psql -h localhost -p 5432 -U monitorix -d monitorix
```

## 📝 Code Standards

### Python (Backend)

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints where possible
- Document functions with docstrings
- Maximum line length: 100 characters
- Use `black` for formatting (if configured)

Example:
```python
from typing import Optional, List
from sqlalchemy.orm import Session

def get_node_by_id(db: Session, node_id: int) -> Optional[Node]:
    """
    Get a node by ID.
    
    Args:
        db: Database session
        node_id: Node ID to lookup
        
    Returns:
        Node object if found, None otherwise
    """
    return db.query(Node).filter(Node.id == node_id).first()
```

### JavaScript/React (Frontend)

- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use functional components with hooks
- Use `const` and `let`, not `var`
- Maximum line length: 100 characters
- Use `prettier` for formatting (if configured)

Example:
```javascript
import { useState, useEffect } from 'react'
import axios from 'axios'

const Nodes = () => {
  const [nodes, setNodes] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchNodes()
  }, [])

  const fetchNodes = async () => {
    try {
      const response = await axios.get('/api/nodes')
      setNodes(response.data)
    } catch (error) {
      console.error('Failed to fetch nodes:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {loading ? <div>Loading...</div> : <NodeList nodes={nodes} />}
    </div>
  )
}

export default Nodes
```

### SQL/Database

- Use SQLAlchemy ORM, not raw SQL
- Use migrations for schema changes
- Document complex queries

### Git

- Use descriptive commit messages
- Commit often, push regularly
- One feature per branch

## 💬 Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code changes)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Tasks (build, config, etc.)

### Examples

```
feat(backend): Add email notification support

Implement email notifications for alerts using SMTP.
Supports multiple email providers.

Closes #42
```

```
fix(frontend): Fix WebSocket reconnection issue

WebSocket now properly reconnects after connection loss.
Added exponential backoff for reconnection attempts.

Fixes #38
```

## 🔍 Pull Requests

### Before Submitting PR

1. ✅ Code compiles and runs without errors
2. ✅ All tests pass (if implemented)
3. ✅ Code follows code standards
4. ✅ Documentation is updated
5. ✅ Commit messages follow conventions

### PR Description

Include:
- What the change does
- Why the change is necessary
- How it was tested
- Screenshots (if UI changes)
- Related issues

### Review Process

1. PR will be reviewed by maintainers
2. Feedback may be given as comments
3. Changes may be requested
4. When approved, PR will be merged

## 📚 Resources

- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [React documentation](https://react.dev/)
- [SQLAlchemy documentation](https://docs.sqlalchemy.org/)
- [Docker documentation](https://docs.docker.com/)

## ❓ Questions?

If you have questions:

1. Check [TODO.md](TODO.md) for known issues
2. Check existing issues
3. Create a new issue with "question" label

---

**Thank you for contributing! 🎉**
