import os
import subprocess, time
from typing import List
from dataclasses import dataclass, field

from codebubble.utils import ResourceLimits, ExecutionStatus, ExecutionResult
from codebubble.executor.base import BaseExecutorConfig, BaseExecutor
from codebubble.sandbox.base import BaseSandboxConfig, BaseSandbox

@dataclass
class PythonExecutorConfig(BaseExecutorConfig):
    interpreter_path: str = "/usr/bin/python3"
    args: List[str] = field(default_factory=list)

class PythonExecutor(BaseExecutor):
    def __init__(self, config: PythonExecutorConfig, sandbox: BaseSandbox):
        super().__init__(config=config, sandbox=sandbox)
        sandbox.config.executable_paths = dict() if sandbox.config.executable_paths is None else sandbox.config.executable_paths
        sandbox.config.executable_paths['python'] = config.interpreter_path
    
    def prepare(self, workspace: str, code: str) -> List[str]:
        script_path = os.path.join(workspace, "main.py")
        with open(script_path, "w") as f:
            f.write(code)
        workspace_in_container = self.sandbox.config.workspace_in_container
        inner_cmd = [os.path.join(workspace_in_container, "python")] + self.config.args + [os.path.join(workspace_in_container, "main.py")]
        return {'inner_cmd': inner_cmd,}
