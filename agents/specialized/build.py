import textwrap
from typing import Dict, Any
from ..base import BaseAgent
from ...core.models import Capability

class BuildAgent(BaseAgent):
    async def initialize(self):
        await self.add_capability(Capability(
            name="generate_dockerfile",
            handler=self._generate_dockerfile
        ))
        
        await self.add_capability(Capability(
            name="generate_docker_compose",
            handler=self._generate_docker_compose
        ))
        
        await self.add_capability(Capability(
            name="generate_requirements",
            handler=self._generate_requirements
        ))

    async def _generate_dockerfile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        language = payload.get("language", "python")
        app_type = payload.get("app_type", "api")
        
        if language == "python":
            dockerfile = self._generate_python_dockerfile(app_type)
        else:
            dockerfile = self._generate_generic_dockerfile(language)
        
        return {
            "content": dockerfile,
            "filename": "Dockerfile"
        }

    async def _generate_docker_compose(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        services = payload.get("services", ["api", "database"])
        
        compose_content = self._generate_compose_file(services)
        
        return {
            "content": compose_content,
            "filename": "docker-compose.yml"
        }

    async def _generate_requirements(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        dependencies = payload.get("dependencies", [])
        language = payload.get("language", "python")
        
        if language == "python":
            content = self._generate_python_requirements(dependencies)
            filename = "requirements.txt"
        else:
            content = "# Requirements for " + language
            filename = "requirements.txt"
        
        return {
            "content": content,
            "filename": filename
        }

    def _generate_python_dockerfile(self, app_type: str) -> str:
        if app_type == "api":
            return textwrap.dedent('''
                FROM python:3.11-slim
                
                WORKDIR /app
                
                COPY requirements.txt .
                RUN pip install --no-cache-dir -r requirements.txt
                
                COPY . .
                
                EXPOSE 8000
                
                CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
            ''').strip()
        else:
            return textwrap.dedent('''
                FROM python:3.11-slim
                
                WORKDIR /app
                
                COPY requirements.txt .
                RUN pip install --no-cache-dir -r requirements.txt
                
                COPY . .
                
                CMD ["python", "main.py"]
            ''').strip()

    def _generate_generic_dockerfile(self, language: str) -> str:
        return textwrap.dedent(f'''
            # Dockerfile for {language} application
            # TODO: Configure base image and build steps for {language}
            
            FROM alpine:latest
            
            WORKDIR /app
            
            COPY . .
            
            # TODO: Add build and run commands
            
            CMD ["echo", "Hello from {language} container"]
        ''').strip()

    def _generate_compose_file(self, services: list) -> str:
        service_configs = []
        
        for service in services:
            if service == "api":
                service_configs.append(self._generate_api_service())
            elif service == "database":
                service_configs.append(self._generate_database_service())
            elif service == "redis":
                service_configs.append(self._generate_redis_service())
        
        services_yaml = "\n\n".join(service_configs)
        
        return textwrap.dedent(f'''
            version: '3.8'
            
            services:
            {services_yaml}
            
            networks:
              app-network:
                driver: bridge
            
            volumes:
              postgres_data:
              redis_data:
        ''').strip()

    def _generate_api_service(self) -> str:
        return textwrap.dedent('''
              api:
                build: .
                ports:
                  - "8000:8000"
                environment:
                  - DATABASE_URL=postgresql://user:password@database:5432/dbname
                  - REDIS_URL=redis://redis:6379
                depends_on:
                  - database
                  - redis
                networks:
                  - app-network
        ''').strip()

    def _generate_database_service(self) -> str:
        return textwrap.dedent('''
              database:
                image: postgres:15
                environment:
                  POSTGRES_DB: dbname
                  POSTGRES_USER: user
                  POSTGRES_PASSWORD: password
                volumes:
                  - postgres_data:/var/lib/postgresql/data
                ports:
                  - "5432:5432"
                networks:
                  - app-network
        ''').strip()

    def _generate_redis_service(self) -> str:
        return textwrap.dedent('''
              redis:
                image: redis:7-alpine
                volumes:
                  - redis_data:/data
                ports:
                  - "6379:6379"
                networks:
                  - app-network
        ''').strip()

    def _generate_python_requirements(self, dependencies: list) -> str:
        default_deps = [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.0.0",
            "sqlalchemy>=2.0.0",
            "alembic>=1.12.0",
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "python-multipart>=0.0.6",
            "psycopg2-binary>=2.9.0",
            "redis>=5.0.0",
            "celery>=5.3.0",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "httpx>=0.25.0"
        ]
        
        if dependencies:
            all_deps = list(set(default_deps + dependencies))
        else:
            all_deps = default_deps
        
        return "\n".join(sorted(all_deps))