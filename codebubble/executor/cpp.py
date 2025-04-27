import os
import subprocess, time
from typing import List
from dataclasses import dataclass, field

from codebubble.utils import ResourceLimits, ExecutionStatus, ExecutionResult
from codebubble.executor.base import BaseExecutorConfig, BaseExecutor
from codebubble.sandbox.base import BaseSandboxConfig, BaseSandbox

@dataclass
class CppExecutorConfig(BaseExecutorConfig):
    compiler_path: str = "/usr/bin/g++"
    compiler_flags: List[str] = field(default_factory=lambda: ["-std=c++17"])

class CppExecutor(BaseExecutor):
    def __init__(self, config: CppExecutorConfig, sandbox: BaseSandbox):
        super().__init__(config=config, sandbox=sandbox)
    
    def prepare(self, workspace: str, code: str) -> List[str]:
        src = os.path.join(workspace, "main.cpp")
        exe = os.path.join(workspace, "main")
        workspace_in_container = self.sandbox.config.workspace_in_container
        inner_cmd = [os.path.join(workspace_in_container, "main")]
        with open(src, "w") as f:
            f.write(code)
        t0 = time.time()
        cmd = [
            self.config.compiler_path,str(src), '-o', exe,
        ] + self.config.compiler_flags
        cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        compile_time = time.time() - t0
        return {
            'inner_cmd': inner_cmd,
            'compile_time': compile_time,
            'compile_return_code': cp.returncode,
            'compile_stdout': cp.stdout.decode(errors='replace'),
            'compile_stderr': cp.stderr.decode(errors='replace'),
        }
