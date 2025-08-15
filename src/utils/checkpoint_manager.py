"""
Persistent checkpoint manager for Kaggle sessions.
Stores vulnerability results and prompts across notebook restarts.
"""

import json
import os
import pickle
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

class CheckpointManager:
    """Manages persistent storage of prompts and vulnerability results."""
    
    def __init__(self, checkpoint_dir: str = "outputs/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths for different types of checkpoints
        self.prompts_file = self.checkpoint_dir / "prompts.json"
        self.vulnerabilities_file = self.checkpoint_dir / "vulnerabilities.json"
        self.session_file = self.checkpoint_dir / "session.pkl"
        
    def save_prompts(self, prompts: List[Dict[str, Any]]) -> None:
        """Save prompts to persistent storage."""
        with open(self.prompts_file, 'w') as f:
            json.dump({
                "prompts": prompts,
                "timestamp": datetime.now().isoformat(),
                "count": len(prompts)
            }, f, indent=2)
    
    def load_prompts(self) -> List[Dict[str, Any]]:
        """Load prompts from persistent storage."""
        if not self.prompts_file.exists():
            return []
        
        try:
            with open(self.prompts_file, 'r') as f:
                data = json.load(f)
                return data.get("prompts", [])
        except Exception:
            return []
    
    def save_vulnerabilities(self, vulnerabilities: List[Dict[str, Any]]) -> None:
        """Save vulnerability results to persistent storage."""
        with open(self.vulnerabilities_file, 'w') as f:
            json.dump({
                "vulnerabilities": vulnerabilities,
                "timestamp": datetime.now().isoformat(),
                "count": len(vulnerabilities)
            }, f, indent=2)
    
    def load_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Load vulnerability results from persistent storage."""
        if not self.vulnerabilities_file.exists():
            return []
        
        try:
            with open(self.vulnerabilities_file, 'r') as f:
                data = json.load(f)
                return data.get("vulnerabilities", [])
        except Exception:
            return []
    
    def save_session_state(self, state: Dict[str, Any]) -> None:
        """Save complete session state for resuming."""
        with open(self.session_file, 'wb') as f:
            pickle.dump({
                "state": state,
                "timestamp": datetime.now().isoformat()
            }, f)
    
    def load_session_state(self) -> Optional[Dict[str, Any]]:
        """Load complete session state for resuming."""
        if not self.session_file.exists():
            return None
        
        try:
            with open(self.session_file, 'rb') as f:
                data = pickle.load(f)
                return data.get("state")
        except Exception:
            return None
    
    def get_checkpoint_info(self) -> Dict[str, Any]:
        """Get information about existing checkpoints."""
        info = {
            "prompts_available": self.prompts_file.exists(),
            "vulnerabilities_available": self.vulnerabilities_file.exists(),
            "session_available": self.session_file.exists(),
            "checkpoint_dir": str(self.checkpoint_dir)
        }
        
        # Add file sizes and timestamps
        for file_path, key in [
            (self.prompts_file, "prompts"),
            (self.vulnerabilities_file, "vulnerabilities"),
            (self.session_file, "session")
        ]:
            if file_path.exists():
                stat = file_path.stat()
                info[f"{key}_size_bytes"] = stat.st_size
                info[f"{key}_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        return info
    
    def clear_checkpoints(self) -> None:
        """Clear all checkpoint files."""
        for file_path in [self.prompts_file, self.vulnerabilities_file, self.session_file]:
            if file_path.exists():
                file_path.unlink()
    
    def export_checkpoints(self, export_dir: str) -> None:
        """Export checkpoints to a directory for Kaggle dataset creation."""
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)
        
        for src_file in [self.prompts_file, self.vulnerabilities_file, self.session_file]:
            if src_file.exists():
                dst_file = export_path / src_file.name
                dst_file.write_bytes(src_file.read_bytes())

# Global instance for easy access
checkpoint_manager = CheckpointManager()
