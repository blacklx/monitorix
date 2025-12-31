"""
Database migration utilities
"""
import subprocess
import sys
import os
from pathlib import Path

def run_migrations():
    """Run database migrations"""
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    try:
        # Run alembic upgrade head
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Migrations applied successfully")
            return True
        else:
            print(f"Migration error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False

if __name__ == "__main__":
    run_migrations()

