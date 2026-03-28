from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
SUMMARY = RESULTS_DIR / "summary.md"
WORKSPACE = ROOT / "superoptix-demo-workspace"
SUPER_BIN = ROOT / ".venv" / "bin" / "super"
PROJECT_PACKAGE_ROOT = WORKSPACE / WORKSPACE.name


def stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log(message: str) -> None:
    print(f"[{stamp()}] {message}")


def section(title: str) -> None:
    print()
    print(f"== {title} ==")


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
    surrealdb_ok = check_tcp("127.0.0.1", 8000)
    ollama_ok = check_tcp("127.0.0.1", 11434)
    log(f"SurrealDB on :8000: {'OK' if surrealdb_ok else 'MISSING'}")
    log(f"Ollama on :11434: {'OK' if ollama_ok else 'MISSING'}")
    if not surrealdb_ok:
        raise RuntimeError("SurrealDB is not reachable on 127.0.0.1:8000. Start Docker and your SurrealDB container first.")
    if with_superoptix:
        if not ollama_ok:
            raise RuntimeError("Ollama is not reachable on 127.0.0.1:11434. Start Ollama first.")
        if not check_ollama_model("qwen3.5:9b"):
            raise RuntimeError("Ollama model qwen3.5:9b is not available. Pull it before using --with-superoptix.")
        log("Ollama model qwen3.5:9b: OK")


def run_standalone(label: str, script_name: str) -> tuple[bool, str]:
    log(f"Running {label} via demo/{script_name}")
    proc = run_cmd(
        [sys.executable, str(ROOT / "demo" / script_name)],
        stream=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    detail = line_for_output(output)
    log(f"{label}: {'PASS' if proc.returncode == 0 else 'FAIL'}")
    print(detail)
    return proc.returncode == 0, detail


def ensure_workspace() -> None:
    if not WORKSPACE.exists():
        log(f"Initializing SuperOptiX workspace at {WORKSPACE.name}")
        proc = run_cmd([str(SUPER_BIN), "init", WORKSPACE.name], cwd=ROOT, stream=True)
        if proc.returncode != 0:
            raise RuntimeError((proc.stdout or "") + (proc.stderr or ""))


def ensure_agent(agent_name: str, framework: str) -> None:
    playbook_dir = PROJECT_PACKAGE_ROOT / "agents" / agent_name / "playbook"
    if not playbook_dir.exists():
        log(f"Pulling packaged agent {agent_name}")
        proc = run_cmd(
            [str(SUPER_BIN), "agent", "pull", agent_name, "--force"],
            cwd=WORKSPACE,
            stream=True,
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stdout or "") + (proc.stderr or ""))
    log(f"Compiling {agent_name} for {framework}")
    proc = run_cmd(
        [str(SUPER_BIN), "agent", "compile", agent_name, "--framework", framework],
        cwd=WORKSPACE,
        stream=True,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stdout or "") + (proc.stderr or ""))


def run_superoptix(label: str, agent_name: str, framework: str) -> tuple[bool, str]:
    ensure_agent(agent_name, framework)
    log(f"Running {label} using {agent_name} ({framework})")
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
    log(f"{label}: {'PASS' if proc.returncode == 0 else 'FAIL'}")
    print(detail)
    return proc.returncode == 0, detail


def write_summary(results: list[tuple[str, bool, str]]) -> None:
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
    log(f"Wrote summary to {SUMMARY}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-superoptix", action="store_true")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    preflight(args.with_superoptix)

    section("TurboAgents Demo")
    log("Starting standalone demo validation")

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
