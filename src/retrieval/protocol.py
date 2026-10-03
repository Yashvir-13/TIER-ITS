import os
from pathlib import Path
from typing import Dict

class ProtocolRetriever:
    """
    Retrieves clinical protocol guidelines (e.g., C-SSRS, SAFE-T) to ground 
    the AI's reporting against established clinical standards.
    """
    def __init__(self, data_dir: str = "data/protocols"):
        self.data_dir = Path(data_dir)
        self._protocols: Dict[str, str] = {}
        self._load_protocols()
        
    def _load_protocols(self):
        if not self.data_dir.exists():
            return
            
        for file_path in self.data_dir.glob("*.txt"):
            protocol_name = file_path.stem.upper()
            self._protocols[protocol_name] = file_path.read_text(encoding="utf-8")
            
    def get_protocol(self, protocol_name: str) -> str:
        """
        Retrieves the full text of a protocol by its name (e.g., 'C-SSRS').
        """
        return self._protocols.get(protocol_name.upper(), "Protocol not found.")
        
    def get_all_protocol_names(self) -> list[str]:
        return list(self._protocols.keys())
