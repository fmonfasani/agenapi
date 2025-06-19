import asyncio
import shutil
import json
import gzip
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from .persistence import PersistenceManager

class BackupManager:
    def __init__(self, persistence: PersistenceManager, backup_dir: str = "./backups"):
        self.persistence = persistence
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self._running = False
        self._task = None

    async def start(self, interval_hours: int = 24):
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._backup_loop(interval_hours))

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

    async def _backup_loop(self, interval_hours: int):
        while self._running:
            try:
                await self.create_backup()
                await self._cleanup_old_backups()
                await asyncio.sleep(interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Backup error: {e}")
                await asyncio.sleep(3600)

    async def create_backup(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"agentapi_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        try:
            db_backup_path = backup_path / "database.db"
            shutil.copy2(self.persistence.db_path, db_backup_path)
            
            metadata = {
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "type": "full_backup"
            }
            
            with open(backup_path / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            archive_path = f"{backup_path}.tar.gz"
            shutil.make_archive(str(backup_path), 'gztar', str(backup_path))
            shutil.rmtree(backup_path)
            
            print(f"Backup created: {archive_path}")
            return archive_path
            
        except Exception as e:
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise e

    async def restore_backup(self, backup_path: str):
        backup_file = Path(backup_path)
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        temp_dir = self.backup_dir / "temp_restore"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        try:
            shutil.unpack_archive(backup_path, temp_dir)
            
            db_backup = temp_dir / "database.db"
            if db_backup.exists():
                shutil.copy2(db_backup, self.persistence.db_path)
                print("Database restored successfully")
            
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    async def list_backups(self) -> List[Dict[str, Any]]:
        backups = []
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)

    async def _cleanup_old_backups(self, keep_count: int = 10):
        backups = await self.list_backups()
        if len(backups) > keep_count:
            for backup in backups[keep_count:]:
                Path(backup["path"]).unlink()
                print(f"Deleted old backup: {backup['name']}")