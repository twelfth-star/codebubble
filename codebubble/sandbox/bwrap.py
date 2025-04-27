from typing import List, Dict, Tuple, Optional
import os
from dataclasses import dataclass, field

from loguru import logger

from codebubble.utils import ResourceLimits, wrap_command_with_time, wrap_command_with_timeout, \
    wrap_command_with_prlimit, ExecutionResult, ExecutionStatus, parse_time_output
from codebubble.sandbox.base import BaseSandboxConfig, BaseSandbox

@dataclass
class BwrapSandboxConfig(BaseSandboxConfig):
    bwrap_path: str = "bwrap"
    bind_mounts: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("/usr", "/usr"), ("/lib", "/lib"), ("/lib64", "/lib64"),
        ("/bin", "/bin"), ("/sbin", "/sbin"), ("/etc", "/etc"), ("/home", "/home"),
    ])
    tmpfs_paths: List[str] = field(default_factory=lambda: ["/tmp"])
    use_proc: bool = True
    use_dev: bool = True
    hostname: str = "sandbox"
    env_vars: Dict[str, str] = field(default_factory=lambda: {"PATH": "/usr/bin"})
    fsize_factor: float = 1.1  # Factor to adjust fsize limit based on max_output_mb

class BwrapSandbox(BaseSandbox):
    def wrap_command(self, inner_cmd: List[str], limits: ResourceLimits) -> List[str]:
        config = self.config
        workspace_in_container = config.workspace_in_container
        
        wrapped = wrap_command_with_time(
            inner_cmd=inner_cmd,
            output_file=os.path.join(workspace_in_container, config.time_output_relative_path),
        )
        wrapped = wrap_command_with_timeout(
            inner_cmd=wrapped,
            time_limit=limits.time_limit,
        )
        wrapped = wrap_command_with_prlimit(
            inner_cmd=wrapped,
            memory_limit=limits.memory_limit,
            fsize_limit=int(limits.max_output_size * config.fsize_factor),
        )
        
        cmd = [config.bwrap_path, "--unshare-all", "--die-with-parent"]
        for src, dst in config.bind_mounts:
            cmd += ["--ro-bind", src, dst]
            
        cmd += ["--bind", str(config.workspace), workspace_in_container, "--chdir", workspace_in_container]
        for name, path in config.executable_paths.items():
            if path and os.path.exists(path):
                container_path = os.path.join(workspace_in_container, name)
                cmd += ["--bind", path, container_path]
            else:
                logger.warning(f"Executable path {path} does not exist. Skipping bind mount.")
        
        for t in config.tmpfs_paths:
            cmd += ["--tmpfs", t]
        if config.use_proc:
            cmd += ["--proc", "/proc"]
        if config.use_dev:
            cmd += ["--dev", "/dev"]
        cmd += ["--hostname", config.hostname]
        for k, v in config.env_vars.items():
            cmd += ["--setenv", k, v]
            
        return cmd + ["--"] + wrapped

    def make_execution_result(
        self,
        full_cmd: List[str],
        stdout_str: Optional[str] = None,
        stderr_str: Optional[str] = None,
        return_code: Optional[int] = None,
        compile_time: Optional[float] = None,
        execution_time: Optional[float] = None,
        limits: Optional[ResourceLimits] = None,
    ) -> ExecutionResult:
        error_info = None
        
        # Parse the time output file
        try:
            time_output_path = os.path.join(self.config.workspace, self.config.time_output_relative_path)
            with open(time_output_path, "r") as f:
                time_output_str = f.read()
                time_output = parse_time_output(time_output_str)
        except Exception as e:
            logger.warning(f"Failed to read time output file. Exception message: {str(e)}")
            time_output = None
        
        # Parse the return code
        status = None
        if return_code == 124:
            status = ExecutionStatus.TIME_LIMIT_EXCEEDED
            execution_time_str = str(execution_time) if execution_time else 'unknown'
            error_info = f"Time limit exceeded. Execution time: {execution_time_str} seconds."
        elif return_code == 137:
            status = ExecutionStatus.MEMORY_LIMIT_EXCEEDED
            peak_memory_str = str(time_output.max_resident_set_size) if (time_output and time_output.max_resident_set_size) else 'unknown'
            error_info = f"Memory limit exceeded. Peak memory: {peak_memory_str} KB."
        elif return_code != 0:
            status = ExecutionStatus.RUNTIME_ERROR
            error_info = f"Unknown runtime error. Return code: {return_code}. stderr: {stderr_str}"
        else:
            status = ExecutionStatus.SUCCESS

        # Check for input/output size limits
        stdout_size = round(len(stdout_str.encode()) / 1024, 2) if stdout_str else 0
        stderr_size = round(len(stderr_str.encode()) / 1024, 2) if stderr_str else 0
        if limits is not None and stdout_size > limits.max_output_size:
            status = ExecutionStatus.OUTPUT_TOO_LARGE
            error_info = f"Standard output too large. Size: {stdout_size} KB."
        if limits is not None and stderr_size > limits.max_output_size:
            status = ExecutionStatus.OUTPUT_TOO_LARGE
            error_info = f"Standard error too large. Size: {stderr_size} KB."

        execution_result = ExecutionResult(
            full_cmd=full_cmd,
            status=status,
            stdout=stdout_str,
            stderr=stderr_str,
            return_code=return_code,
            compile_time=compile_time,
            execution_time=execution_time,
            error_info=error_info,
            time_result=time_output,
        )
        
        return execution_result