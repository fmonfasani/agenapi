import psutil
import asyncio
from typing import Dict, Any
from .models import SystemMetrics

class ResourceManager:
    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def initialize(self):
        self._resources["system"] = {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total
        }

    async def acquire_resource(self, resource_id: str, agent_name: str) -> bool:
        lock = self._get_lock(resource_id)
        acquired = lock.locked()
        if not acquired:
            await lock.acquire()
            self._resources[f"{resource_id}_owner"] = agent_name
        return not acquired

    async def release_resource(self, resource_id: str, agent_name: str):
        if self._resources.get(f"{resource_id}_owner") == agent_name:
            lock = self._get_lock(resource_id)
            if lock.locked():
                lock.release()
            self._resources.pop(f"{resource_id}_owner", None)

    async def get_metrics(self) -> SystemMetrics:
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage('/').percent,
            active_agents=len([k for k in self._resources.keys() if k.endswith("_owner")]),
            message_queue_size=0  # TODO: implement from message bus
        )

    def _get_lock(self, resource_id: str) -> asyncio.Lock:
        if resource_id not in self._locks:
            self._locks[resource_id] = asyncio.Lock()
        return self._locks[resource_id]