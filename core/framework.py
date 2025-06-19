import asyncio
from typing import Dict, List, Optional, Any
from .models import AgentConfig, SystemMetrics, Status
from .registry import AgentRegistry
from .message_bus import MessageBus
from .resource_manager import ResourceManager

class AgentFramework:
    def __init__(self):
        self.registry = AgentRegistry()
        self.message_bus = MessageBus()
        self.resource_manager = ResourceManager()
        self.status = Status.IDLE
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self):
        if self._running:
            return
        
        self.status = Status.RUNNING
        self._running = True
        
        await self.message_bus.start()
        await self.resource_manager.initialize()
        
        self._tasks.append(asyncio.create_task(self._monitor_loop()))

    async def stop(self):
        if not self._running:
            return
            
        self._running = False
        self.status = Status.STOPPED
        
        for task in self._tasks:
            task.cancel()
        
        await self.message_bus.stop()
        await self.registry.stop_all_agents()

    async def register_agent(self, agent_class: type, config: AgentConfig):
        agent = agent_class(config, self.message_bus, self.resource_manager)
        await self.registry.register(agent)
        return agent

    async def get_metrics(self) -> SystemMetrics:
        return await self.resource_manager.get_metrics()

    async def _monitor_loop(self):
        while self._running:
            try:
                metrics = await self.get_metrics()
                await self.message_bus.publish_event("system.metrics", metrics.__dict__)
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(5)