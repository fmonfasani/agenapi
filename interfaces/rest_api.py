from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import jwt
from datetime import datetime, timedelta
from ..core.framework import AgentFramework
from ..core.models import AgentConfig, AgentMessage, MessageType, SystemMetrics
from ..agents.factory import AgentFactory
from ..systems.security import SecurityManager

class CreateAgentRequest(BaseModel):
    name: str
    agent_type: str
    capabilities: List[str] = []
    resources: Dict[str, Any] = {}

class SendMessageRequest(BaseModel):
    receiver: str
    capability: str
    payload: Dict[str, Any] = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class APIServer:
    def __init__(self, framework: AgentFramework):
        self.app = FastAPI(title="AgentAPI", version="1.0.0")
        self.framework = framework
        self.security = SecurityManager()
        self.bearer_scheme = HTTPBearer()
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

    def _setup_routes(self):
        @self.app.post("/auth/login")
        async def login(request: LoginRequest):
            user = await self.security.authenticate_user(request.username, request.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            token = self.security.create_access_token({"sub": user.username})
            return {"access_token": token, "token_type": "bearer"}

        @self.app.get("/agents")
        async def list_agents(current_user: dict = Depends(self._get_current_user)):
            return await self.framework.registry.list_agents()

        @self.app.post("/agents")
        async def create_agent(
            request: CreateAgentRequest,
            current_user: dict = Depends(self._get_current_user)
        ):
            config = AgentConfig(
                name=request.name,
                capabilities=request.capabilities,
                resources=request.resources
            )
            
            try:
                agent = AgentFactory.create_agent(
                    request.agent_type,
                    config,
                    self.framework.message_bus,
                    self.framework.resource_manager
                )
                await self.framework.registry.register(agent)
                return {"message": "Agent created successfully", "name": request.name}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.delete("/agents/{agent_name}")
        async def delete_agent(
            agent_name: str,
            current_user: dict = Depends(self._get_current_user)
        ):
            await self.framework.registry.unregister(agent_name)
            return {"message": "Agent deleted successfully"}

        @self.app.post("/messages/send")
        async def send_message(
            request: SendMessageRequest,
            current_user: dict = Depends(self._get_current_user)
        ):
            message = AgentMessage(
                type=MessageType.REQUEST,
                sender=current_user["username"],
                receiver=request.receiver,
                capability=request.capability,
                payload=request.payload
            )
            
            await self.framework.message_bus.send_message(message)
            return {"message": "Message sent successfully", "id": message.id}

        @self.app.get("/metrics")
        async def get_metrics(current_user: dict = Depends(self._get_current_user)):
            metrics = await self.framework.get_metrics()
            return metrics.__dict__

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        @self.app.get("/agent-types")
        async def list_agent_types():
            return {"types": AgentFactory.list_agent_types()}

    async def _get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        try:
            payload = jwt.decode(credentials.credentials, self.security.secret_key, algorithms=["HS256"])
            username = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            return {"username": username}
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")