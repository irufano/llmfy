from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Optional

from llmfy.flow_engine.checkpointer.base_checkpointer import (
    BaseCheckpointer,
    Checkpoint,
)


class InMemoryCheckpointer(BaseCheckpointer):
    """In-memory checkpoint storage backend."""
    
    def __init__(self):
        """Initialize the memory checkpointer."""
        # Storage: session_id -> list of checkpoints
        self._storage: Dict[str, List[Checkpoint]] = defaultdict(list)
        # Index: checkpoint_id -> (session_id, checkpoint)
        self._index: Dict[str, tuple[str, Checkpoint]] = {}
    
    async def save(self, checkpoint: Checkpoint) -> None:
        """
        Save a checkpoint to memory.
        
        Args:
            checkpoint: The checkpoint to save
        """
        # Deep copy to prevent external modifications
        checkpoint_copy = deepcopy(checkpoint)
        
        session_id = checkpoint.metadata.session_id
        checkpoint_id = checkpoint.metadata.checkpoint_id
        
        # Add to storage
        self._storage[session_id].append(checkpoint_copy)
        
        # Sort by timestamp (newest first)
        self._storage[session_id].sort(
            key=lambda c: c.metadata.timestamp,
            reverse=True
        )
        
        # Add to index
        self._index[checkpoint_id] = (session_id, checkpoint_copy)
    
    async def load(self, session_id: str, checkpoint_id: Optional[str] = None) -> Optional[Checkpoint]:
        """
        Load a checkpoint from memory.
        
        Args:
            session_id: The session ID
            checkpoint_id: Specific checkpoint ID, or None for latest
            
        Returns:
            The checkpoint if found, None otherwise
        """
        if checkpoint_id:
            # Load specific checkpoint
            if checkpoint_id in self._index:
                stored_session_id, checkpoint = self._index[checkpoint_id]
                if stored_session_id == session_id:
                    return deepcopy(checkpoint)
            return None
        else:
            # Load latest checkpoint for thread
            if session_id in self._storage and self._storage[session_id]:
                return deepcopy(self._storage[session_id][0])
            return None
    
    async def list(self, session_id: str, limit: int = 10) -> list[Checkpoint]:
        """
        List checkpoints for a thread.
        
        Args:
            session_id: The session ID
            limit: Maximum number of checkpoints to return
            
        Returns:
            List of checkpoints, newest first
        """
        if session_id not in self._storage:
            return []
        
        checkpoints = self._storage[session_id][:limit]
        return [deepcopy(c) for c in checkpoints]
    
    async def delete(self, session_id: str, checkpoint_id: Optional[str] = None) -> None:
        """
        Delete checkpoint(s) from memory.
        
        Args:
            session_id: The session ID
            checkpoint_id: Specific checkpoint ID, or None to delete all for session
        """
        if checkpoint_id:
            # Delete specific checkpoint
            if checkpoint_id in self._index:
                stored_session_id, checkpoint = self._index[checkpoint_id]
                if stored_session_id == session_id:
                    # Remove from storage
                    self._storage[session_id] = [
                        c for c in self._storage[session_id]
                        if c.metadata.checkpoint_id != checkpoint_id
                    ]
                    # Remove from index
                    del self._index[checkpoint_id]
                    
                    # Clean up empty thread storage
                    if not self._storage[session_id]:
                        del self._storage[session_id]
        else:
            # Delete all checkpoints for thread
            if session_id in self._storage:
                # Remove from index
                for checkpoint in self._storage[session_id]:
                    checkpoint_id = checkpoint.metadata.checkpoint_id
                    if checkpoint_id in self._index:
                        del self._index[checkpoint_id]
                
                # Remove from storage
                del self._storage[session_id]
    
    async def clear_all(self) -> None:
        """Clear all checkpoints from memory."""
        self._storage.clear()
        self._index.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_sessions": len(self._storage),
            "total_checkpoints": len(self._index),
            "checkpoints_per_session": {
                session_id: len(checkpoints)
                for session_id, checkpoints in self._storage.items()
            }
        }