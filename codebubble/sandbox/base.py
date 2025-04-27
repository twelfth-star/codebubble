import shutil
import os
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional

from codebubble.utils import ResourceLimits, ExecutionResult

@dataclass
class BaseSandboxConfig:
    workspace: str = './workspace'
    workspace_in_container: str = "/app"
    backend: str = "bwrap"
    executable_paths: Dict[str, str] = field(default_factory=dict)
    time_output_relative_path: str = "time_output.txt"

class BaseSandbox(ABC):
    def __init__(self, config: BaseSandboxConfig):
        config.workspace = os.path.abspath(config.workspace)
        self.config = config
        
    def reset_workspace(self):
        workspace = self.config.workspace
        if os.path.exists(workspace):
            shutil.rmtree(workspace)
        os.makedirs(workspace, exist_ok=True)
        
    @abstractmethod
    def wrap_command(self, inner_cmd: List[str], limits: ResourceLimits) -> List[str]:
        """Wraps the command with sandbox isolation and resource controls."""
        pass
    
    @abstractmethod
    def make_execution_result(
        self,
        full_cmd: List[str],
        stdout_str: Optional[str] = None,
        stderr_str: Optional[str] = None,
        return_code: Optional[int] = None,
        compile_time: Optional[float] = None,
        execution_time: Optional[float] = None,
    ) -> ExecutionResult:
        pass