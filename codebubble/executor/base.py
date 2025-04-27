import time
import subprocess
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from loguru import logger

from codebubble.utils import ResourceLimits, ExecutionStatus, ExecutionResult
from codebubble.sandbox.base import BaseSandboxConfig, BaseSandbox

@dataclass
class BaseExecutorConfig:
    language: str = "python"

class BaseExecutor(ABC):
    def __init__(self, config: BaseExecutorConfig, sandbox: BaseSandbox):
        self.config = config
        self.sandbox = sandbox

    @abstractmethod
    def prepare(self, workspace: str, code: str) -> List[str]:
        pass

    def single_run(self, code: str, input_str: str, limits: ResourceLimits, prepare_result: Dict[str, Any]) -> ExecutionResult:
        inner_cmd = prepare_result.get("inner_cmd", None)
        assert inner_cmd is not None, "Inner command must be provided in prepare_result"
        compile_time = prepare_result.get("compile_time", None)
        
        full_cmd = self.sandbox.wrap_command(inner_cmd=inner_cmd, limits=limits)
        
        workspace = self.sandbox.config.workspace
        stdout_path = os.path.join(workspace, "stdout.txt")
        stderr_path = os.path.join(workspace, "stderr.txt")
        
        t0 = time.time()
        try:
            with open(stdout_path, "wb") as stdout_file, open(stderr_path, "wb") as stderr_file:
                proc = subprocess.run(
                    full_cmd,
                    input=input_str.encode(),
                    stdout=stdout_file,
                    stderr=stderr_file
                )
        except Exception as e:
            if os.path.exists(stdout_path):
                os.remove(stdout_path)
            if os.path.exists(stderr_path):
                os.remove(stderr_path)
            return ExecutionResult(
                full_cmd=full_cmd,
                status=ExecutionStatus.ERROR,
                error_info=f"Execution failed due to unexpected error. Execution message: {str(e)}",
                compile_time=compile_time,
            )
        execution_time = time.time() - t0
        
        with open(stdout_path, "rb") as stdout_file:
            stdout_data = stdout_file.read()
            stdout_str = stdout_data.decode(errors="replace")
        with open(stderr_path, "rb") as stderr_file:
            stderr_data = stderr_file.read()
            stderr_str = stderr_data.decode(errors="replace")
        
        return_code = proc.returncode
        execution_result = self.sandbox.make_execution_result(
            full_cmd=full_cmd,
            stdout_str=stdout_str,
            stderr_str=stderr_str,
            return_code=return_code,
            compile_time=compile_time,
            execution_time=execution_time
        )
        if os.path.exists(stdout_path):
            os.remove(stdout_path)
        if os.path.exists(stderr_path):
            os.remove(stderr_path)
        return execution_result
        
        
    def run(self, code: str, inputs: List[str], limits: ResourceLimits) -> List[ExecutionResult]:
        self.sandbox.reset_workspace()
        workspace = self.sandbox.config.workspace
        prepare_result = self.prepare(workspace, code)
        compile_time = prepare_result.get("compile_time", None)
        compile_return_code = prepare_result.get("compile_return_code", None)
        if compile_return_code is not None and compile_return_code != 0:
            compile_stderr = prepare_result.get("compile_stderr", '')
            self.sandbox.reset_workspace()
            return [ExecutionResult(
                status=ExecutionStatus.COMPILE_ERROR,
                compile_time=compile_time,
                error_info=f"Compilation failed. Return code: {compile_return_code}. Stderr: {compile_stderr}",
            ) for _ in inputs]
        
        results = []
        t0 = time.time()
        for input_str in inputs:
            if time.time() - t0 > limits.overall_time_limit:
                execution_result = ExecutionResult(
                    status=ExecutionStatus.SKIPPED,
                    compile_time=compile_time,
                    error_info="Skipped due to overall time limit exceeded."
                )
                results.append(execution_result)
                continue
            if len(input_str.encode()) > limits.max_input_size * 1024:
                execution_result = ExecutionResult(
                    status=ExecutionStatus.INPUT_TOO_LARGE,
                    compile_time=compile_time,
                    error_info="Input too large."
                )
                results.append(execution_result)
                continue
            execution_result = self.single_run(
                code=code,
                input_str=input_str,
                limits=limits,
                prepare_result=prepare_result
            )
            results.append(execution_result)
        self.sandbox.reset_workspace()
        return results