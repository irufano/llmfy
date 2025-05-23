from copy import deepcopy
from datetime import datetime, timedelta
from threading import Lock, Timer
from typing import Any, Dict, List, Optional


class MemoryManager:
    def __init__(
        self,
        extend_list: bool = False,
        cleanup: bool = True,
        cleanup_time: int = 9000,
    ):
        """MemoryManager

        Args:
            extend_list (bool, optional): Always extended list value.
                If there is key with list value then list will extended with new value.
            cleanup (bool, optional): run cleanup memories after `cleanup_time`
            cleanup_time (int, optional): default clean up time 90000 seconds = 1 day + 1 hour = 86400s + 3600s
        """
        self._memories: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.always_extend_list = extend_list
        self._timestamps = {}  # Timestamps to track last usage of threads
        self._cleanup_task = None  # Reference to the cleanup timer
        self._using_cleanup = cleanup
        self._cleanup_time = cleanup_time

    def get_memory(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get memory for a specific thread."""
        with self._lock:
            return deepcopy(self._memories.get(thread_id))

    def deep_merge(self, existing: Any, new_data: Any) -> Any:
        """Recursively merge dictionaries and append new unique items to lists."""
        if isinstance(existing, dict) and isinstance(new_data, dict):
            for key, value in new_data.items():
                if key in existing:
                    existing[key] = self.deep_merge(existing[key], value)
                else:
                    existing[key] = deepcopy(value)
        elif isinstance(existing, list) and isinstance(new_data, list):
            # Append only new unique dictionaries (avoid duplicates)
            existing_dicts = {
                frozenset(d.items()) for d in existing if isinstance(d, dict)
            }
            for item in new_data:
                if (
                    isinstance(item, dict)
                    and frozenset(item.items()) not in existing_dicts
                ):
                    existing.append(deepcopy(item))
                elif item not in existing:  # For non-dict items
                    existing.append(deepcopy(item))
        else:
            # If neither a dict nor a list, just overwrite the value
            existing = deepcopy(new_data)

        return existing

    def update_memory(
        self,
        thread_id: str,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update memory for a specific thread."""
        with self._lock:
            # Update the last usage timestamp
            self._timestamps[thread_id] = datetime.now()

            if self._using_cleanup:
                # Ensure cleanup task is running
                if self._cleanup_task is None:
                    self._start_cleanup_task(interval=self._cleanup_time)

            # Check thread_id
            if thread_id not in self._memories:
                self._memories[thread_id] = deepcopy(state)
            else:
                if self.always_extend_list:
                    self._memories[thread_id] = self.deep_merge(
                        self._memories[thread_id], state
                    )
                else:
                    self._memories[thread_id].update(deepcopy(state))

            # hah = deepcopy(self._memories.get(thread_id))
            # pprint.pp(f"\nMEMORY: {thread_id}= {self._memories}")
            # print(f"\nCHECK: {self._memories}")
            return self._memories[thread_id]

    def delete_memory(self, thread_id: str) -> None:
        """Delete memory for a specific thread."""
        with self._lock:
            if thread_id in self._memories:
                del self._memories[thread_id]

    def list_threads(self) -> List[str]:
        """List all thread IDs with active memories."""
        with self._lock:
            return list(self._memories.keys())

    def _start_cleanup_task(self, interval: int):
        """Start a periodic task to clean up inactive threads.

        Args:
            interval (int, optional): Interval in seconds for running the cleanup task.
                (default 90000 seconds = 1 day + 1 hour = 86400s + 3600s)
        """

        def cleanup():
            self._remove_inactive_threads(interval)
            # Schedule the next cleanup only if there are threads left
            if self._memories:
                self._cleanup_task = Timer(interval, cleanup)
                self._cleanup_task.start()
            else:
                self._cleanup_task = None

        if self._cleanup_task is None:  # Prevent multiple timers
            self._cleanup_task = Timer(interval, cleanup)
            self._cleanup_task.start()

    def _remove_inactive_threads(self, interval: int):
        print("---- CLEAN-UP RUNNING ----")
        with self._lock:  # Ensure thread-safe access
            now = datetime.now()
            inactive_threads = [
                thread_id
                for thread_id, last_used in self._timestamps.items()
                if now - last_used > timedelta(seconds=interval)
            ]
            for thread_id in inactive_threads:
                del self._memories[thread_id]
                del self._timestamps[thread_id]

            # Stop cleanup task if no threads remain
            if not self._memories:
                self.cleanup_task = None
                print("No threads left. Stopping cleanup task.")
                print("---- CLEAN-UP STOPPED ----")
