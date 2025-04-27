from enum import Enum, auto
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from dataclasses import dataclass, field

@dataclass
class ResourceLimits:
    time_limit: float = 5                    # time limit per input in seconds
    overall_time_limit: float = 30           # time limit for all inputs in seconds
    memory_limit: int = 256 * 1024           # memory limit in KB
    max_input_size: int = 2 * 1024           # max input size in KB
    max_output_size: int = 2 * 1024          # max output size in KB
    
    def __repr__(self) -> str:
        return (f"ResourceLimits(time_limit={self.time_limit}s, overall_time_limit={self.overall_time_limit}s, "
                f"memory_limit={self.memory_limit}KB, max_input_size={self.max_input_size}KB, "
                f"max_output_size={self.max_output_size}KB)")
    def __str__(self) -> str:
        return self.__repr__()


class ExecutionStatus(Enum):
    SUCCESS = auto()
    TIME_LIMIT_EXCEEDED = auto()
    MEMORY_LIMIT_EXCEEDED = auto()
    INPUT_TOO_LARGE = auto()
    OUTPUT_TOO_LARGE = auto()
    RUNTIME_ERROR = auto()
    COMPILE_ERROR = auto()
    SKIPPED = auto()
    ERROR = auto()


@dataclass
class TimeResult:
    command: Optional[str] = None
    elapsed_time: Optional[float] = None  # in seconds
    user_cpu_time: Optional[float] = None
    system_cpu_time: Optional[float] = None
    cpu_percentage: Optional[str] = None
    avg_total_mem: Optional[int] = None
    avg_shared_mem: Optional[int] = None
    avg_unshared_data: Optional[int] = None
    avg_unshared_stack: Optional[int] = None
    page_reclaims: Optional[int] = None
    page_faults: Optional[int] = None
    swaps: Optional[int] = None
    block_input_ops: Optional[int] = None
    block_output_ops: Optional[int] = None
    ipc_msgs_sent: Optional[int] = None
    ipc_msgs_received: Optional[int] = None
    signals_received: Optional[int] = None
    voluntary_ctxt_switches: Optional[int] = None
    involuntary_ctxt_switches: Optional[int] = None
    max_resident_set_size: Optional[int] = None
    exit_status: Optional[int] = None
    
    def __repr__(self) -> str:
        if self.command:
            command_str = self.command
            command_str = (command_str[:100] + '...') if len(command_str) > 100 else command_str
        else:
            command_str = None
        elapsed_time_str = f"{self.elapsed_time:.2f}s" if self.elapsed_time else None
        user_cpu_time_str = f"{self.user_cpu_time:.2f}s" if self.user_cpu_time else None
        system_cpu_time_str = f"{self.system_cpu_time:.2f}s" if self.system_cpu_time else None
        cpu_percentage_str = self.cpu_percentage if self.cpu_percentage else None
        return (f"TimeResult(command={command_str!r}, elapsed_time={elapsed_time_str}, "
                f"user_cpu_time={user_cpu_time_str}, system_cpu_time={system_cpu_time_str}, "
                f"cpu_percentage={cpu_percentage_str})")
    def __str__(self) -> str:
        return self.__repr__()
    
class ExecutionResult(BaseModel):
    full_cmd: Optional[List[str]] = None
    status: Optional[ExecutionStatus] = None
    return_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_time: Optional[float] = None
    execution_time: Optional[float] = None
    error_info: Optional[str] = None
    time_result: Optional[TimeResult] = None
    
    def __repr__(self) -> str:
        stdout_preview = (self.stdout[:100] + '...') if self.stdout and len(self.stdout) > 100 else self.stdout
        stderr_preview = (self.stderr[:100] + '...') if self.stderr and len(self.stderr) > 100 else self.stderr
        compile_time_str = f"{self.compile_time:.2f}s" if self.compile_time else None
        execution_time_str = f"{self.execution_time:.2f}s" if self.execution_time else None
        if self.error_info:
            error_info_str = self.error_info
            error_info_str = error_info_str.replace('\n', r'\n')
            error_info_str = (error_info_str[:100] + '...') if error_info_str and len(error_info_str) > 100 else error_info_str
        else:
            error_info_str = None
        return (f'ExecutionResult(status={self.status}, return_code={self.return_code}, '
                f'error_info={error_info_str!r}, '
                f'compile_time={compile_time_str}, execution_time={execution_time_str}, '
                f'stdout={stdout_preview!r}, stderr={stderr_preview!r})')
    def __str__(self) -> str:
        return self.__repr__()

def parse_time_output(output_str: str) -> TimeResult:
    def parse_elapsed_time(t: str) -> float:
        parts = t.split(":")
        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        else:
            return float(parts[0])

    result = TimeResult()
    lines = output_str.splitlines()
    for line in lines:
        key_value = line.strip().split(':', 1)
        if len(key_value) != 2:
            continue
        key, value = key_value[0].strip(), key_value[1].strip()

        if key == "Command":
            result.command = value
        elif key == "Elapsed time":
            try: result.elapsed_time = parse_elapsed_time(value)
            except: pass
        elif key == "User CPU time":
            try: result.user_cpu_time = float(value)
            except: pass
        elif key == "System CPU time":
            try: result.system_cpu_time = float(value)
            except: pass
        elif key == "CPU Percentage":
            result.cpu_percentage = value
        elif key == "Avg total memory usage":
            try: result.avg_total_mem = int(value.split()[0])
            except: pass
        elif key == "Avg shared memory size":
            try: result.avg_shared_mem = int(value.split()[0])
            except: pass
        elif key == "Avg unshared data size":
            try: result.avg_unshared_data = int(value.split()[0])
            except: pass
        elif key == "Avg unshared stack size":
            try: result.avg_unshared_stack = int(value.split()[0])
            except: pass
        elif key == "Page reclaims (soft page faults)":
            try: result.page_reclaims = int(value)
            except: pass
        elif key == "Page faults (hard page faults)":
            try: result.page_faults = int(value)
            except: pass
        elif key == "Swaps":
            try: result.swaps = int(value)
            except: pass
        elif key == "Block input operations":
            try: result.block_input_ops = int(value)
            except: pass
        elif key == "Block output operations":
            try: result.block_output_ops = int(value)
            except: pass
        elif key == "IPC messages sent":
            try: result.ipc_msgs_sent = int(value)
            except: pass
        elif key == "IPC messages received":
            try: result.ipc_msgs_received = int(value)
            except: pass
        elif key == "Signals received":
            try: result.signals_received = int(value)
            except: pass
        elif key == "Voluntary context switches":
            try: result.voluntary_ctxt_switches = int(value)
            except: pass
        elif key == "Involuntary context switches":
            try: result.involuntary_ctxt_switches = int(value)
            except: pass
        elif key == "Maximum resident set size":
            try: result.max_resident_set_size = int(value.split()[0])
            except: pass
        elif key == "Exit status":
            try: result.exit_status = int(value)
            except: pass

    return result

def wrap_command_with_time(inner_cmd: List[str], output_file: str) -> List[str]:
    format_string = (
        "Command: %C\n"
        "Elapsed time: %E\n"
        "User CPU time: %U\n"
        "System CPU time: %S\n"
        "CPU Percentage: %P\n"
        "Avg total memory usage: %K KB\n"
        "Avg shared memory size: %D KB\n"
        "Avg unshared data size: %p KB\n"
        "Avg unshared stack size: %t KB\n"
        "Page reclaims (soft page faults): %R\n"
        "Page faults (hard page faults): %F\n"
        "Swaps: %W\n"
        "Block input operations: %I\n"
        "Block output operations: %O\n"
        "IPC messages sent: %r\n"
        "IPC messages received: %s\n"
        "Signals received: %k\n"
        "Voluntary context switches: %w\n"
        "Involuntary context switches: %c\n"
        "Maximum resident set size: %M KB\n"
        "Exit status: %x"
    )
    return [
        "/usr/bin/time",
        "-f", format_string,
        "-o", output_file
    ] + inner_cmd


def wrap_command_with_timeout(inner_cmd: List[str], time_limit: float) -> List[str]:
    """ Wraps the command with a timeout.
    
    Args:
        inner_cmd (List[str]): The command to be executed.
        time_limit (float): The time limit in seconds.
    """
    
    cmd = [
        "timeout", "--foreground", f"{time_limit}s",
    ] + inner_cmd
    return cmd

def wrap_command_with_prlimit(inner_cmd: List[str], memory_limit: int, fsize_limit: int) -> List[str]:
    """ Wraps the command with resource limits using prlimit.
    
    Args:
        inner_cmd (List[str]): The command to be executed.
        memory_limit (int): The memory limit in KB.
        fsize_limit (int): The file size limit in KB.
    """
    cmd = [
        "prlimit",
        f"--as={memory_limit * 1024}",
        f"--fsize={fsize_limit * 1024}",
        "--",
    ] + inner_cmd
    return cmd