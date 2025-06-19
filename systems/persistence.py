import aiosqlite
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..core.models import AgentMessage, SystemMetrics

class PersistenceManager:
    def __init__(self, db_path: str = "agentapi.db"):
        self.db_path = db_path
        self._lock = asyncio.Lock()

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    name TEXT PRIMARY KEY,
                    config TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    sender TEXT,
                    receiver TEXT,
                    capability TEXT,
                    payload TEXT,
                    timestamp TIMESTAMP,
                    correlation_id TEXT
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_usage REAL,
                    active_agents INTEGER,
                    message_queue_size INTEGER,
                    timestamp TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS resources (
                    id TEXT PRIMARY KEY,
                    data TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            await db.commit()

    async def save_agent(self, name: str, config: Dict[str, Any], status: str):
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                now = datetime.now().isoformat()
                await db.execute('''
                    INSERT OR REPLACE INTO agents (name, config, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, json.dumps(config), status, now, now))
                await db.commit()

    async def load_agent(self, name: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT config, status, created_at, updated_at FROM agents WHERE name = ?',
                (name,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "name": name,
                        "config": json.loads(row[0]),
                        "status": row[1],
                        "created_at": row[2],
                        "updated_at": row[3]
                    }
                return None

    async def save_message(self, message: AgentMessage):
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO messages (id, type, sender, receiver, capability, payload, timestamp, correlation_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    message.id, message.type.value, message.sender, message.receiver,
                    message.capability, json.dumps(message.payload),
                    message.timestamp.isoformat(), message.correlation_id
                ))
                await db.commit()

    async def get_messages(self, agent_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT id, type, sender, receiver, capability, payload, timestamp, correlation_id
                FROM messages
                WHERE sender = ? OR receiver = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (agent_name, agent_name, limit)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row[0], "type": row[1], "sender": row[2], "receiver": row[3],
                        "capability": row[4], "payload": json.loads(row[5]),
                        "timestamp": row[6], "correlation_id": row[7]
                    }
                    for row in rows
                ]

    async def save_metrics(self, metrics: SystemMetrics):
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO metrics (cpu_percent, memory_percent, disk_usage, active_agents, message_queue_size, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.cpu_percent, metrics.memory_percent, metrics.disk_usage,
                    metrics.active_agents, metrics.message_queue_size, metrics.timestamp.isoformat()
                ))
                await db.commit()

    async def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        cutoff = datetime.now() - timedelta(hours=hours)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT cpu_percent, memory_percent, disk_usage, active_agents, message_queue_size, timestamp
                FROM metrics
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (cutoff.isoformat(),)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "cpu_percent": row[0], "memory_percent": row[1], "disk_usage": row[2],
                        "active_agents": row[3], "message_queue_size": row[4], "timestamp": row[5]
                    }
                    for row in rows
                ]

    async def save_resource(self, resource_id: str, data: Dict[str, Any]):
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                now = datetime.now().isoformat()
                await db.execute('''
                    INSERT OR REPLACE INTO resources (id, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (resource_id, json.dumps(data), now, now))
                await db.commit()

    async def load_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT data FROM resources WHERE id = ?',
                (resource_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return None