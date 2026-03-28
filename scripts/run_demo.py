from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
SUMMARY = RESULTS_DIR / "summary.md"
REFERENCE_WORKSPACE = ROOT / "superoptix-demo-workspace"
WORKSPACE = ROOT / "superoptix-demo-runtime"
SUPER_BIN = ROOT / ".venv" / "bin" / "super"
PROJECT_PACKAGE_ROOT = WORKSPACE / WORKSPACE.name

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


def style(text: str, *codes: str) -> str:
    return "".join(codes) + text + RESET


def stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log(message: str) -> None:
    print(f"{style(f'[{stamp()}]', DIM)} {message}")


def section(title: str) -> None:
    print()
    print(style(f"== {title} ==", BOLD, BLUE))


def status(label: str, ok: bool) -> str:
    return style(label, BOLD, GREEN if ok else RED)


def note(message: str) -> None:
    print(style(message, YELLOW))


def format_cmd(cmd: list[str]) -> str:
    rendered: list[str] = []
    for part in cmd:
        if part == str(sys.executable):
            rendered.append("python")
        elif part == str(SUPER_BIN):
            rendered.append("super")
        else:
            try:
                path = Path(part)
                if path.is_absolute():
                    try:
                        rendered.append(str(path.relative_to(ROOT)))
                    except ValueError:
                        rendered.append(part)
                else:
                    rendered.append(part)
            except Exception:
                rendered.append(part)
    return " ".join(rendered)


def run_cmd(
    cmd: list[str], *, cwd: Path | None = None, stream: bool = False
) -> subprocess.CompletedProcess[str]:
    if stream:
        log(f"$ {format_cmd(cmd)}")
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        chunks: list[str] = []
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="")
            chunks.append(line)
        returncode = proc.wait()
        return subprocess.CompletedProcess(
            cmd,
            returncode,
            stdout="".join(chunks),
            stderr="",
        )

    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def line_for_output(output: str) -> str:
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("1. ") or "retrieved_response:" in line or "Validation Status:" in line:
            return line
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[-1] if lines else "no output"


def check_tcp(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except OSError:
        return False


def check_ollama_model(model_name: str) -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False
    return any(model.get("name") == model_name for model in data.get("models", []))


def preflight(with_superoptix: bool) -> None:
    section("Preflight")
    note("Checking the local services required for this demo before we start.")
    surrealdb_ok = check_tcp("127.0.0.1", 8000)
    ollama_ok = check_tcp("127.0.0.1", 11434)
    log(f"SurrealDB on :8000: {status('OK', surrealdb_ok) if surrealdb_ok else status('MISSING', False)}")
    log(f"Ollama on :11434: {status('OK', ollama_ok) if ollama_ok else status('MISSING', False)}")
    if not surrealdb_ok:
        raise RuntimeError("SurrealDB is not reachable on 127.0.0.1:8000. Start Docker and your SurrealDB container first.")
    if with_superoptix:
        if not ollama_ok:
            raise RuntimeError("Ollama is not reachable on 127.0.0.1:11434. Start Ollama first.")
        if not check_ollama_model("qwen3.5:9b"):
            raise RuntimeError("Ollama model qwen3.5:9b is not available. Pull it before using --with-superoptix.")
        log(f"Ollama model qwen3.5:9b: {status('OK', True)}")


def reset_results() -> None:
    if RESULTS_DIR.exists():
        note("Resetting previous results so this run starts clean.")
        shutil.rmtree(RESULTS_DIR)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_standalone(label: str, script_name: str) -> tuple[bool, str]:
    note(f"Next: run {label} with the TurboQuant-style compressed index path and print the top retrieval hits.")
    log(f"{style('Running', BOLD, CYAN)} {label} via demo/{script_name}")
    proc = run_cmd(
        [sys.executable, str(ROOT / "demo" / script_name)],
        stream=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    detail = line_for_output(output)
    log(f"{label}: {status('PASS', proc.returncode == 0) if proc.returncode == 0 else status('FAIL', False)}")
    print(style(detail, YELLOW))
    return proc.returncode == 0, detail


def ensure_workspace() -> None:
    if WORKSPACE.exists():
        note("Resetting the previous runtime SuperOptiX workspace so compiled artifacts do not leak across runs.")
        shutil.rmtree(WORKSPACE)
    note("Next: create an isolated runtime SuperOptiX workspace without touching the checked-in reference output.")
    log(f"{style('Initializing', BOLD, CYAN)} SuperOptiX workspace at {WORKSPACE.name}")
    proc = run_cmd([str(SUPER_BIN), "init", WORKSPACE.name], cwd=ROOT, stream=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stdout or "") + (proc.stderr or ""))
    if REFERENCE_WORKSPACE.exists():
        log(f"{style('Reference', BOLD, BLUE)} generated code remains available in {REFERENCE_WORKSPACE.name}")


def ensure_agent(agent_name: str, framework: str) -> None:
    playbook_dir = PROJECT_PACKAGE_ROOT / "agents" / agent_name / "playbook"
    if not playbook_dir.exists():
        note(f"Next: pull the packaged {framework} demo agent into the runtime workspace.")
        log(f"{style('Pulling', BOLD, CYAN)} packaged agent {agent_name}")
        proc = run_cmd(
            [str(SUPER_BIN), "agent", "pull", agent_name, "--force"],
            cwd=WORKSPACE,
            stream=True,
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stdout or "") + (proc.stderr or ""))
    note(f"Next: compile the {framework} pipeline so it is ready to run with TurboQuant-style TurboAgents-backed retrieval.")
    log(f"{style('Compiling', BOLD, CYAN)} {agent_name} for {framework}")
    proc = run_cmd(
        [str(SUPER_BIN), "agent", "compile", agent_name, "--framework", framework],
        cwd=WORKSPACE,
        stream=True,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stdout or "") + (proc.stderr or ""))


def run_superoptix(label: str, agent_name: str, framework: str) -> tuple[bool, str]:
    ensure_agent(agent_name, framework)
    note(f"Next: run the {framework} demo and surface the grounded result produced through the TurboQuant-style retrieval path.")
    log(f"{style('Running', BOLD, CYAN)} {label} using {agent_name} ({framework})")
    proc = run_cmd(
        [
            str(SUPER_BIN),
            "agent",
            "run",
            agent_name,
            "--framework",
            framework,
            "--goal",
            "What is NEON-FOX-742?",
        ],
        cwd=WORKSPACE,
        stream=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    detail = line_for_output(output)
    log(f"{label}: {status('PASS', proc.returncode == 0) if proc.returncode == 0 else status('FAIL', False)}")
    print(style(detail, YELLOW))
    return proc.returncode == 0, detail


def write_summary(results: list[tuple[str, bool, str]]) -> None:
    note("Final step: write a short summary so the whole run is easy to review.")
    lines = [
        "# TurboAgents Demo Summary",
        "",
        "This summary is generated by `scripts/run_demo.py`.",
        "",
    ]
    for name, ok, detail in results:
        lines.append(f"- {name}: {'passed' if ok else 'failed'}")
        lines.append(f"  - {detail}")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"{style('Summary', BOLD, GREEN)} written to {SUMMARY}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-superoptix", action="store_true")
    args = parser.parse_args()

    preflight(args.with_superoptix)
    reset_results()

    section("TurboAgents Demo")
    log("Starting standalone demo validation with the TurboQuant-style compressed retrieval path")

    results: list[tuple[str, bool, str]] = []

    for name, script in [
        ("Standalone LanceDB", "standalone_lancedb_demo.py"),
        ("Standalone SurrealDB", "standalone_surrealdb_demo.py"),
    ]:
        ok, detail = run_standalone(name, script)
        results.append((name, ok, detail))
        print()

    if args.with_superoptix:
        section("SuperOptiX Integrations")
        log("Starting framework integration validation")
        ensure_workspace()
        for name, agent, framework in [
            ("SuperOptiX DSPy", "rag_surrealdb_dspy_demo", "dspy"),
            ("SuperOptiX Pydantic AI", "rag_surrealdb_pydanticai_demo", "pydantic-ai"),
            ("SuperOptiX OpenAI Agents SDK", "rag_surrealdb_openai_demo", "openai"),
        ]:
            ok, detail = run_superoptix(name, agent, framework)
            results.append((name, ok, detail))
            print()

    write_summary(results)


if __name__ == "__main__":
    main()
