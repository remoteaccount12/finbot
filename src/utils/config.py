

import os
import yaml
from pathlib import Path
# from .config import Config

class Config:
    def __init__(self,mode="prod"):
        config_path = Path(__file__).resolve().parents[2] / "configs" / "prod.yaml"
        with config_path.open() as f:
            base = yaml.safe_load(f)
        self._cfg = base
    def __getattr__(self,name):
        if name in self._cfg:
            return self._cfg[name]

