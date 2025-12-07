import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint."""
    checkpoint_id: str
    thread_id: str
    timestamp: datetime
    node_name: str
    step: int



@dataclass
class Checkpoint:
    """Represents a saved state checkpoint."""
    metadata: CheckpointMetadata
    state: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary for storage."""
        return {
            "checkpoint_id": self.metadata.checkpoint_id,
            "thread_id": self.metadata.thread_id,
            "timestamp": self.metadata.timestamp.isoformat(),
            "node_name": self.metadata.node_name,
            "step": self.metadata.step,
            "state": self._serialize_state(self.state)
        }
    
    @staticmethod
    def _serialize_state(state: Dict[str, Any]) -> str:
        """Serialize state to JSON string, handling custom objects."""
        def default_serializer(obj):
            if hasattr(obj, '__dict__'):
                return {
                    '__type__': obj.__class__.__name__,
                    '__module__': obj.__class__.__module__,
                    'data': obj.__dict__
                }
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(state, default=default_serializer)
    
    @staticmethod
    def _deserialize_state(state_str: str) -> Dict[str, Any]:
        """Deserialize state from JSON string, reconstructing custom objects."""
        import importlib
        
        def object_hook(dct):
            if '__type__' in dct and '__module__' in dct and 'data' in dct:
                # Reconstruct the custom object
                try:
                    module = importlib.import_module(dct['__module__'])
                    cls = getattr(module, dct['__type__'])
                    
                    # Handle different object construction patterns
                    if hasattr(cls, '__init__'):
                        # Try to create instance from data dict
                        obj_data = dct['data']
                        
                        # Check if class accepts **kwargs
                        try:
                            obj = cls(**obj_data)
                            return obj
                        except TypeError:
                            # If direct kwargs don't work, try creating empty instance
                            # and setting attributes
                            try:
                                obj = cls.__new__(cls)
                                for key, value in obj_data.items():
                                    setattr(obj, key, value)
                                return obj
                            except Exception as _:
                                # If all else fails, return the dict
                                return dct
                except (ImportError, AttributeError) as _:
                    # If we can't import the class, return the dict representation
                    return dct
            return dct
        
        return json.loads(state_str, object_hook=object_hook)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create checkpoint from dictionary."""
        metadata = CheckpointMetadata(
            checkpoint_id=data["checkpoint_id"],
            thread_id=data["thread_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            node_name=data["node_name"],
            step=data["step"]
        )
        state = cls._deserialize_state(data["state"])
        return cls(metadata=metadata, state=state)



class BaseCheckpointer(ABC):
    """Base class for checkpoint storage backends."""
    
    @abstractmethod
    async def save(self, checkpoint: Checkpoint) -> None:
        """
        Save a checkpoint.
        
        Args:
            checkpoint: The checkpoint to save
        """
        pass
    
    @abstractmethod
    async def load(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Checkpoint]:
        """
        Load a checkpoint.
        
        Args:
            thread_id: The thread ID
            checkpoint_id: Specific checkpoint ID, or None for latest
            
        Returns:
            The checkpoint if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list(self, thread_id: str, limit: int = 10) -> List[Checkpoint]:
        """
        List checkpoints for a thread.
        
        Args:
            thread_id: The thread ID
            limit: Maximum number of checkpoints to return
            
        Returns:
            List of checkpoints, newest first
        """
        pass
    
    @abstractmethod
    async def delete(self, thread_id: str, checkpoint_id: Optional[str] = None) -> None:
        """
        Delete checkpoint(s).
        
        Args:
            thread_id: The thread ID
            checkpoint_id: Specific checkpoint ID, or None to delete all for thread
        """
        pass
    
    @abstractmethod
    async def clear_all(self) -> None:
        """Clear all checkpoints from storage."""
        pass