import asyncio
from typing import Dict, List, Optional
from .models import Status

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def register(self, agent):
        async with self._lock:
            self._agents[agent.name] = agent
            await agent.start()

    async def unregister(self, name: str):
        async with self._lock:
            if name in self._agents:
                await self._agents[name].stop()
                del self._agents[name]

    async def get_agent(self, name: str):
        return self._agents.get(name)

    async def list_agents(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": agent.name,
                "status": agent.status.value,
                "capabilities": list(agent.capabilities.keys())
            }
            for agent in self._agents.values()
        ]

    async def stop_all_agents(self):
        tasks = [agent.stop() for agent in self._agents.values()]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._agents.clear()