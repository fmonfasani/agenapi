import asyncio
import psutil
from typing import Dict, Any, List, Callable
from datetime import datetime, timedelta
from ..core.models import SystemMetrics

class Alert:
    def __init__(self, name: str, condition: Callable[[SystemMetrics], bool], action: Callable):
        self.name = name
        self.condition = condition
        self.action = action
        self.last_triggered = None

class MonitoringManager:
    def __init__(self):
        self.alerts: List[Alert] = []
        self.metrics_history: List[SystemMetrics] = []
        self._running = False
        self._task = None

    def add_alert(self, alert: Alert):
        self.alerts.append(alert)

    async def start(self):
        if self._running:
            return
        
        self._running = True
        self._setup_default_alerts()
        self._task = asyncio.create_task(self._monitoring_loop())

    async def stop(self):
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def _setup_default_alerts(self):
        self.add_alert(Alert(
            "high_cpu",
            lambda m: m.cpu_percent > 80,
            self._high_cpu_alert
        ))
        
        self.add_alert(Alert(
            "high_memory",
            lambda m: m.memory_percent > 85,
            self._high_memory_alert
        ))
        
        self.add_alert(Alert(
            "low_disk_space",
            lambda m: m.disk_usage > 90,
            self._low_disk_alert
        ))

    async def _monitoring_loop(self):
        while self._running:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-500:]
                
                await self._check_alerts(metrics)
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(5)

    async def _collect_metrics(self) -> SystemMetrics:
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage('/').percent,
            active_agents=0,  # TODO: get from framework
            message_queue_size=0  # TODO: get from message bus
        )

    async def _check_alerts(self, metrics: SystemMetrics):
        for alert in self.alerts:
            if alert.condition(metrics):
                now = datetime.now()
                if not alert.last_triggered or (now - alert.last_triggered) > timedelta(minutes=5):
                    await alert.action(metrics)
                    alert.last_triggered = now

    async def _high_cpu_alert(self, metrics: SystemMetrics):
        print(f"ALERT: High CPU usage detected: {metrics.cpu_percent}%")

    async def _high_memory_alert(self, metrics: SystemMetrics):
        print(f"ALERT: High memory usage detected: {metrics.memory_percent}%")

    async def _low_disk_alert(self, metrics: SystemMetrics):
        print(f"ALERT: Low disk space detected: {metrics.disk_usage}% used")

    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff]
        
        if not recent_metrics:
            return {}
        
        return {
            "avg_cpu": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            "avg_memory": sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            "avg_disk": sum(m.disk_usage for m in recent_metrics) / len(recent_metrics),
            "max_cpu": max(m.cpu_percent for m in recent_metrics),
            "max_memory": max(m.memory_percent for m in recent_metrics),
            "sample_count": len(recent_metrics)
        }

    async def health_check(self) -> Dict[str, Any]:
        latest = self.metrics_history[-1] if self.metrics_history else None
        
        status = "healthy"
        if latest:
            if latest.cpu_percent > 90 or latest.memory_percent > 95 or latest.disk_usage > 95:
                status = "critical"
            elif latest.cpu_percent > 70 or latest.memory_percent > 80 or latest.disk_usage > 80:
                status = "warning"
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "latest_metrics": latest.__dict__ if latest else None,
            "alerts_configured": len(self.alerts)
        }