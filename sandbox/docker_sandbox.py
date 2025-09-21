import io
import re
import tarfile
import time
from typing import Literal

import docker

FORBIDDEN_PATTERNS = [
    r"\bimport\s+os\b", r"\bimport\s+subprocess\b", r"\bimport\s+socket\b",
    r"os\.system\(", r"subprocess\.", r"open\(\s*['\"]/(etc|proc|sys|dev)"
]
FAST_LIMITS = dict(mem_limit="256m", cpu_quota=100000, cpu_period=100000)  # 1 CPU
SECURE_LIMITS = dict(mem_limit="128m", cpu_quota=50000, cpu_period=100000)  # 0.5 CPU
IMAGE = "python:3.11-slim"


def run_python(
        code: str,
        profile: Literal["fast", "secure"] = "secure",
        timeout: int = 3
) -> dict:
    if any(re.search(p, code) for p in FORBIDDEN_PATTERNS):
        return {"stdout": "", "stderr": "Blocked by policy", "exit_code": 255}
    client = docker.from_env()
    limits = FAST_LIMITS if profile == "fast" else SECURE_LIMITS
    wrapper = """#!/usr/bin/env python3
import runpy, sys
sys.dont_write_bytecode = True
sys.modules.clear()
runpy.run_path('/tmp/script.py', run_name='__main__')
"""
    c = client.containers.run(
        IMAGE, command=["python", "-I", "-S", "-B", "/tmp/runner.py"], detach=True, remove=True,
        network_disabled=True, read_only=True, mem_limit=limits["mem_limit"],
        cpu_quota=limits["cpu_quota"], cpu_period=limits["cpu_period"],
        security_opt=["no-new-privileges"], pids_limit=256,
        tmpfs={"/tmp": "rw,size=16m,exec,nr_inodes=4096"},
    )
    c.put_archive("/tmp", _make_tar({"runner.py": wrapper.encode(), "script.py": code.encode()}))
    result = c.wait(timeout=timeout)
    exit_code = int(result.get("StatusCode", 1))
    stdout = c.logs(stdout=True, stderr=False).decode(errors="ignore")
    stderr = c.logs(stdout=False, stderr=True).decode(errors="ignore")
    try:
        c.remove(force=True)
    except Exception:
        pass
    return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}


def _make_tar(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            info.mtime = int(time.time())
            tar.addfile(info, io.BytesIO(data))
    buf.seek(0)
    return buf.read()
