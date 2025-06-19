from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import uuid

class Status(Enum):
    IDLE = "idle"
    RUNNING = "running"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"

class MessageType(Enum):
    COMMAND = "command"
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"

@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.REQUEST
    sender: str = ""
    receiver: str = ""
    capability: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None

@dataclass
class Capability:
    name: str
    handler: Callable
    schema: Dict[str, Any] = field(default_factory=dict)
    permissions: List[Permission] = field(default_factory=list)

@dataclass
class AgentConfig:
    name: str
    capabilities: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    max_concurrent: int = 10
    auto_save: bool = True

@dataclass
class SystemMetrics:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_usage: float = 0.0
    active_agents: int = 0
    message_queue_size: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class User:
    id: str
    username: str
    permissions: List[Permission]
    created_at: datetime = field(default_factory=datetime.now)