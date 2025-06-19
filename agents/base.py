import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..core.models import AgentConfig, AgentMessage, Status, Capability

class BaseAgent(ABC):
    def __init__(self, config: AgentConfig, message_bus, resource_manager):
        self.name = config.name
        self.config = config
        self.message_bus = message_bus
        self.resource_manager = resource_manager
        self.status = Status.IDLE
        self.capabilities: Dict[str, Capability] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self._running:
            return
            
        self._running = True
        self.status = Status.RUNNING
        await self.initialize()
        self._task = asyncio.create_task(self._message_loop())

    async def stop(self):
        if not self._running:
            return
            
        self._running = False
        self.status = Status.STOPPED
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    @abstractmethod
    async def initialize(self):
        pass

    async def add_capability(self, capability: Capability):
        self.capabilities[capability.name] = capability

    async def _message_loop(self):
        async for message in self.message_bus.receive_messages(self.name):
            try:
                await self._handle_message(message)
            except Exception as e:
                print(f"Error handling message: {e}")

    async def _handle_message(self, message: AgentMessage):
        if message.capability in self.capabilities:
            capability = self.capabilities[message.capability]
            result = await capability.handler(message.payload)
            
            if message.type == MessageType.REQUEST:
                response = AgentMessage(
                    type=MessageType.RESPONSE,
                    sender=self.name,
                    receiver=message.sender,
                    capability=message.capability,
                    payload={"result": result},
                    correlation_id=message.id
                )
                await self.message_bus.send_message(response)
                