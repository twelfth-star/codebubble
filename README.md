# CodeBubble: 🧪 Sandbox Your AI-Generated Code

`CodeBubble` is a lightweight, rootless sandboxing library for running untrusted code—perfect for taming wild AI-generated programs on Linux.

---

## Why CodeBubble? 🔥

- **AI Code Mayhem**: AI-generated snippets can contain infinite loops, memory bombs, or malicious operations like `rm -rf /`. One rogue program can crash your experiments or compromise your server.
- **Rootless Bwrap Magic**: Leverages [Bubblewrap (bwrap)](https://github.com/containers/bubblewrap) for unprivileged isolation (no `sudo` required), ideal for shared lab or school servers.
- **Detailed Metrics**: Captures exit status, timing, CPU/memory usage, I/O stats, and error classifications in structured Python objects.
- **Multi-Language Out-of-the-Box**: Ships with Python and C++ executors; extendable to Java, Go, Rust, and more via `BaseExecutor`.

---

## 📦 Installation

### 1. Install the Python package

```bash
pip install codebubble
```

### 2. Install Bubblewrap (bwrap)

**With root:**

```bash
sudo apt-get update
sudo apt install bubblewrap
```

**Without root (build from source):**

```bash
pip install meson ninja
export PATH="$HOME/.local/bin:$PATH"

git clone https://github.com/containers/bubblewrap.git
cd bubblewrap
meson setup build --prefix=$HOME/.local
meson compile -C build
meson install -C build

~/.local/bin/bwrap --version # check installation
bwrap --version # check installation
```

---

## 🚀 Quick Start

### Python Executor

```python
from codebubble.utils import ResourceLimits
from codebubble.sandbox.bwrap import BwrapSandbox, BwrapSandboxConfig
from codebubble.executor.python import PythonExecutor, PythonExecutorConfig

# 1. Configure a bwrap sandbox
workspace = "./py_workspace" # any empty directory
bwrap_path = "bwrap" # or the absolute path to bwrap
sb_config = BwrapSandboxConfig(workspace=workspace, bwrap_path=bwrap_path)
sandbox = BwrapSandbox(sb_config)

# 2. Set up Python executor
py_config = PythonExecutorConfig(interpreter_path='/usr/bin/python3')
executor = PythonExecutor(py_config, sandbox)

# 3. Run untrusted Python code
test_code = """
print("Sandboxed Python ✅")
a, b = map(int, input().split())
s = a + b
print(f"Sum: {s}")
"""
inputs = [
    "1 2\n",
    "3 4\n",
    "5 6\n"
]
limits = ResourceLimits(
    time_limit=3,             # seconds per input
    overall_time_limit=10,    # seconds for all inputs
    memory_limit=64 * 1024,   # KB of RAM
    max_input_size=2 * 1024,  # KB of input data
    max_output_size=2 * 1024   # KB of output data
)
results = executor.run(test_code, inputs, limits)
for r in results:
    print(r)
```

### C++ Executor

```python
from codebubble.utils import ResourceLimits
from codebubble.sandbox.bwrap import BwrapSandbox, BwrapSandboxConfig
from codebubble.executor.cpp import CppExecutor, CppExecutorConfig

# 1. Configure a bwrap sandbox
workspace = "./cpp_workspace" # any empty directory
bwrap_path = "bwrap" # or the absolute path to bwrap
sb_config = BwrapSandboxConfig(workspace=workspace, bwrap_path=bwrap_path)
sandbox = BwrapSandbox(sb_config)

# 2. Set up C++ executor with custom compile flags
cpp_config = CppExecutorConfig(
    compiler_path='/usr/bin/g++',
    compiler_flags=['-std=c++17', '-O2', '-Wall']
)
executor = CppExecutor(cpp_config, sandbox)

# 3. Compile & run untrusted C++ code
test_code = """
#include <iostream>
int main() {
    std::cout << "Sandboxed C++ ✅" << std::endl;
    int a, b;
    std::cin >> a >> b;
    int s = a + b;
    std::cout << "Sum: " << s << std::endl;
    return 0;
}
"""
inputs = [
    "1 2\n",
    "3 4\n",
    "5 6\n"
]
limits = ResourceLimits(
    time_limit=3,             # seconds per input
    overall_time_limit=10,    # seconds for all inputs
    memory_limit=64 * 1024,   # KB of RAM
    max_input_size=2 * 1024,  # KB of input data
    max_output_size=2 * 1024   # KB of output data
)
results = executor.run(test_code, inputs, limits)
for r in results:
    print(r)
```

---

## ⚙️ Configuration

### ResourceLimits

| Parameter            | Description            | Default      |
| -------------------- | ---------------------- | ------------ |
| `time_limit`         | Seconds per run        | `5.0`        |
| `overall_time_limit` | Seconds for all inputs | `30.0`       |
| `memory_limit`       | KB of RAM              | `256 * 1024` |
| `max_input_size`     | KB of input data       | `2 * 1024`   |
| `max_output_size`    | KB of output data      | `2 * 1024`   |

### BwrapSandboxConfig

| Parameter      | Description                         | Default                 |
| -------------- | ----------------------------------- | ----------------------- |
| `bind_mounts`  | Read-only mounts `(host,container)` | `[('/usr','/usr'),...]` |
| `tmpfs_paths`  | Paths mounted as tmpfs              | `['/tmp']`              |
| `use_proc`     | Mount `/proc`                       | `True`                  |
| `use_dev`      | Mount `/dev`                        | `True`                  |
| `env_vars`     | Env vars inside sandbox             | `{'PATH':'/usr/bin'}`   |
| `hostname`     | Sandbox hostname                    | `'sandbox'`             |
| `fsize_factor` | File-size limit multiplier          | `1.1`                   |

## 📊 Metrics

### ExecutionResult

| Field            | Type                        | Description                                         |
| ---------------- | --------------------------- | --------------------------------------------------- |
| `full_cmd`       | List[str]                   | The full command executed (including wrappers)      |
| `status`         | ExecutionStatus             | One of `SUCCESS`, `TIME_LIMIT_EXCEEDED`, etc.       |
| `return_code`    | int                         | Process exit code                                   |
| `stdout`         | str                         | Captured standard output                            |
| `stderr`         | str                         | Captured standard error                             |
| `compile_time`   | float (sec) (optional)      | Time spent compiling (if applicable)                |
| `execution_time` | float (sec) (optional)      | Wall-clock execution time                           |
| `error_info`     | str (optional)              | Human-readable error description                    |
| `time_result`    | TimeResult (optional)       | Parsed resource metrics object                      |

### TimeResult

| Metric                                                  | Type / Unit      | Description                         |
| ------------------------------------------------------- | ---------------- | ----------------------------------- |
| `elapsed_time`                                          | float (sec)      | Wall-clock time                     |
| `user_cpu_time` / `system_cpu_time`                     | float (sec)      | CPU user and system times           |
| `cpu_percentage`                                        | string           | CPU usage percentage                |
| `avg_total_mem`                                         | int (KB)         | Average total memory usage          |
| `avg_shared_mem` / `avg_unshared_data` / `avg_unshared_stack` | int (KB)     | Breakdown of shared/unshared memory |
| `page_reclaims` / `page_faults`                         | int              | Soft / hard page faults             |
| `swaps`                                                 | int              | Number of swap operations           |
| `block_input_ops` / `block_output_ops`                  | int              | Block I/O operations                |
| `ipc_msgs_sent` / `ipc_msgs_received`                   | int              | IPC messages sent / received        |
| `signals_received`                                      | int              | Number of signals received          |
| `voluntary_ctxt_switches` / `involuntary_ctxt_switches` | int              | Context switches                    |
| `max_resident_set_size`                                 | int (KB)         | Peak resident set size              |
| `exit_status`                                           | int              | Command exit code                   |

---

## 💡 How It Works

1. **Sandbox Creation**: Bubblewrap spawns an unprivileged container, mounting only essential directories and isolating the workspace.
2. **Resource Guards**: Uses `prlimit` to cap memory/file sizes and `timeout` to enforce execution time limits.
3. **Metric Collection**: Wraps the command with `/usr/bin/time -f <format>` to gather detailed stats in `time_output.txt`.
4. **Execution Pipeline**:
   - **Reset:** cleanup workspace before each run.
   - **Prepare**: write source files (and compile for C++).
   - **Run**: execute inside the sandbox, capturing `stdout`/`stderr`.
   - **Collect**: parse metrics via `parse_time_output()` into a `TimeResult` object.
   - **Aggregate**: build `ExecutionResult` with status, outputs, timings, and metrics.

