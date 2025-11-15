"""
Simple script to run the API server.

For development use only.
Production should use uvicorn directly or gunicorn.
"""

import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.api_title} v{settings.api_version}")
    print(f"Environment: {settings.environment}")
    print(f"Server: http://{settings.host}:{settings.port}")
    print(f"Docs: http://{settings.host}:{settings.port}/docs")
    print()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
