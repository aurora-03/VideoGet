import threading
from typing import Dict, Any, Optional


class TaskManager:
    """任务管理器 - 管理下载任务的状态"""

    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_task(self, task_id: str, url: str) -> None:
        """创建新任务"""
        with self._lock:
            self._tasks[task_id] = {
                "url": url,
                "status": "pending",
                "progress": 0,
                "filename": None,
                "download_url": None,
                "error": None
            }

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> None:
        """更新任务状态"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].update(kwargs)

    def set_status(self, task_id: str, status: str) -> None:
        """设置任务状态"""
        self.update_task(task_id, status=status)

    def set_progress(self, task_id: str, progress: int) -> None:
        """设置下载进度"""
        normalized = min(max(progress, 0), 100)
        with self._lock:
            if task_id not in self._tasks:
                return
            current = int(self._tasks[task_id].get("progress", 0))
            self._tasks[task_id]["progress"] = max(current, normalized)

    def set_complete(self, task_id: str, filename: str, download_url: str) -> None:
        """标记任务完成"""
        self.update_task(
            task_id,
            status="completed",
            progress=100,
            filename=filename,
            download_url=download_url
        )

    def set_error(self, task_id: str, error: str) -> None:
        """标记任务错误"""
        self.update_task(
            task_id,
            status="error",
            error=error
        )
