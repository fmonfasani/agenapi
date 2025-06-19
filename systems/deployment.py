import textwrap
from pathlib import Path
from typing import Dict, Any

class DeploymentManager:
    def __init__(self, project_name: str = "agentapi"):
        self.project_name = project_name

    def generate_kubernetes_manifests(self) -> Dict[str, str]:
        return {
            "namespace.yaml": self._generate_namespace(),
            "deployment.yaml": self._generate_deployment(),
            "service.yaml": self._generate_service(),
            "configmap.yaml": self._generate_configmap(),
            "secret.yaml": self._generate_secret(),
            "ingress.yaml": self._generate_ingress()
        }

    def generate_docker_compose(self) -> str:
        return textwrap.dedent(f'''
            version: '3.8'
            
            services:
              {self.project_name}:
                build: .
                ports:
                  - "8000:8000"
                environment:
                  - DATABASE_URL=postgresql://postgres:password@postgres:5432/{self.project_name}
                  - REDIS_URL=redis://redis:6379
                  - JWT_SECRET=your-secret-key-change-this
                depends_on:
                  - postgres
                  - redis
                volumes:
                  - ./data:/app/data
                restart: unless-stopped
                networks:
                  - app-network
            
              postgres:
                image: postgres:15
                environment:
                  POSTGRES_DB: {self.project_name}
                  POSTGRES_USER: postgres
                  POSTGRES_PASSWORD: password
                volumes:
                  - postgres_data:/var/lib/postgresql/data
                networks:
                  - app-network
                restart: unless-stopped
            
              redis:
                image: redis:7-alpine
                volumes:
                  - redis_data:/data
                networks:
                  - app-network
                restart: unless-stopped
            
            networks:
              app-network:
                driver: bridge
            
            volumes:
              postgres_data:
              redis_data:
        ''').strip()

    def _generate_namespace(self) -> str:
        return textwrap.dedent(f'''
            apiVersion: v1
            kind: Namespace
            metadata:
              name: {self.project_name}
        ''').strip()

    def _generate_deployment(self) -> str:
        return textwrap.dedent(f'''
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: {self.project_name}
              namespace: {self.project_name}
            spec:
              replicas: 3
              selector:
                matchLabels:
                  app: {self.project_name}
              template:
                metadata:
                  labels:
                    app: {self.project_name}
                spec:
                  containers:
                  - name: {self.project_name}
                    image: {self.project_name}:latest
                    ports:
                    - containerPort: 8000
                    env:
                    - name: DATABASE_URL
                      valueFrom:
                        secretKeyRef:
                          name: {self.project_name}-secrets
                          key: database-url
                    - name: JWT_SECRET
                      valueFrom:
                        secretKeyRef:
                          name: {self.project_name}-secrets
                          key: jwt-secret
                    livenessProbe:
                      httpGet:
                        path: /health
                        port: 8000
                      initialDelaySeconds: 30
                      periodSeconds: 10
                    readinessProbe:
                      httpGet:
                        path: /health
                        port: 8000
                      initialDelaySeconds: 5
                      periodSeconds: 5
        ''').strip()

    def _generate_service(self) -> str:
        return textwrap.dedent(f'''
            apiVersion: v1
            kind: Service
            metadata:
              name: {self.project_name}-service
              namespace: {self.project_name}
            spec:
              selector:
                app: {self.project_name}
              ports:
              - protocol: TCP
                port: 80
                targetPort: 8000
              type: ClusterIP
        ''').strip()

    def _generate_configmap(self) -> str:
        return textwrap.dedent(f'''
            apiVersion: v1
            kind: ConfigMap
            metadata:
              name: {self.project_name}-config
              namespace: {self.project_name}
            data:
              LOG_LEVEL: "INFO"
              MAX_WORKERS: "4"
              BACKUP_SCHEDULE: "0 2 * * *"
        ''').strip()

    def _generate_secret(self) -> str:
        return textwrap.dedent(f'''
            apiVersion: v1
            kind: Secret
            metadata:
              name: {self.project_name}-secrets
              namespace: {self.project_name}
            type: Opaque
            data:
              database-url: cG9zdGdyZXNxbDovL3Bvc3RncmVzOnBhc3N3b3JkQHBvc3RncmVzOjU0MzIvYWdlbnRhcGk=
              jwt-secret: eW91ci1zZWNyZXQta2V5LWNoYW5nZS10aGlz
        ''').strip()

    def _generate_ingress(self) -> str:
        return textwrap.dedent(f'''
            apiVersion: networking.k8s.io/v1
            kind: Ingress
            metadata:
              name: {self.project_name}-ingress
              namespace: {self.project_name}
              annotations:
                nginx.ingress.kubernetes.io/rewrite-target: /
            spec:
              rules:
              - host: {self.project_name}.local
                http:
                  paths:
                  - path: /
                    pathType: Prefix
                    backend:
                      service:
                        name: {self.project_name}-service
                        port:
                          number: 80
        ''').strip()

    def save_manifests(self, output_dir: str = "./k8s"):
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        manifests = self.generate_kubernetes_manifests()
        for filename, content in manifests.items():
            (output_path / filename).write_text(content)
        
        (Path(output_dir).parent / "docker-compose.yml").write_text(self.generate_docker_compose())
        
        print(f"Deployment files generated in {output_dir}")