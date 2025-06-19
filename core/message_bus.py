import asyncio
import json
from typing import Dict, List, Callable, Any
from .models import AgentMessage, MessageType

class MessageBus:
    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._running = False

    async def start(self):
        self._running = True

    async def stop(self):
        self._running = False
        for queue in self._queues.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

    async def send_message(self, message: AgentMessage):
        if not self._running:
            return
            
        receiver_queue = self._get_queue(message.receiver)
        await receiver_queue.put(message)

    async def receive_messages(self, agent_name: str) -> AsyncIterator[AgentMessage]:
        queue = self._get_queue(agent_name)
        while self._running:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield message
            except asyncio.TimeoutError:
                continue

    async def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def publish_event(self, event_type: str, data: Any):
        if event_type in self._subscribers:
            tasks = [callback(data) for callback in self._subscribers[event_type]]
            await asyncio.gather(*tasks, return_exceptions=True)

    def _get_queue(self, agent_name: str) -> asyncio.Queue:
        if agent_name not in self._queues:
            self._queues[agent_name] = asyncio.Queue()
        return self._queues[agent_name]