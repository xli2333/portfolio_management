import json
import os
import uuid
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, base_path="knowledge_base"):
        self.file_path = os.path.join(base_path, "deep_research_tasks.json")
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def _load_tasks(self):
        try:
            if not os.path.exists(self.file_path):
                return {}
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
            return {}

    def _save_tasks(self, tasks):
        try:
            # Atomic write to prevent corruption
            temp_path = f"{self.file_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=2)
            os.replace(temp_path, self.file_path)
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")

    def create_task(self, symbol, mode):
        tasks = self._load_tasks()
        task_id = str(uuid.uuid4())
        
        tasks[task_id] = {
            "id": task_id,
            "symbol": symbol,
            "mode": mode,
            "status": "pending",
            "progress": "初始化任务...",
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self._save_tasks(tasks)
        return task_id

    def update_task(self, task_id, status=None, progress=None, result=None, error=None):
        tasks = self._load_tasks()
        if task_id not in tasks:
            return False
            
        if status:
            tasks[task_id]["status"] = status
        if progress:
            tasks[task_id]["progress"] = progress
        if result:
            tasks[task_id]["result"] = result
        if error:
            tasks[task_id]["error"] = error
            
        tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()
        
        # Cleanup old tasks (keep last 50) if list gets too long
        if len(tasks) > 100:
            sorted_tasks = sorted(tasks.items(), key=lambda x: x[1]['created_at'], reverse=True)
            tasks = dict(sorted_tasks[:50])
            
        self._save_tasks(tasks)
        return True

    def get_task(self, task_id):
        tasks = self._load_tasks()
        return tasks.get(task_id)
