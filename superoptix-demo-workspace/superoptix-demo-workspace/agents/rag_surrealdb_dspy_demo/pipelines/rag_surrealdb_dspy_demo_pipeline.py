"""
RagSurrealdbDspyDemo Agent - Native DSPy Program

Auto-generated from SuperSpec playbook using SuperOptiX compiler.
Framework: DSPy (Minimal Native Profile)
Generated: N/A

This file intentionally contains DSPy-native program code:
- Signature
- Explicit LM setup (dspy.LM + dspy.configure)
- Module with forward()
- build_program() factory

SuperOptiX runner handles playbook loading/execution orchestration.
"""

import inspect
import json
from pathlib import Path

import dspy
from superoptix.runners.dspy_runtime_helpers import (
    build_builtin_tools as _runtime_build_builtin_tools,
    postprocess_prediction as _runtime_postprocess_prediction,
    validate_prediction_result as _runtime_validate_prediction_result,
)

# Compile-time runtime policy flag injected by SuperOptiX compiler.
ALLOW_LOCAL_OLLAMA = True
RUNTIME_MODE = "auto"
PROVIDER_OVERRIDE = None
MODEL_OVERRIDE = None

# Visible optimization knobs for this pipeline (used by SuperOptiX runner).
GEPA_CONFIG = {
    "enabled": True,
    "auto": "light",
    "task_model": "qwen3.5:9b",
    "teacher_model": "qwen3.5:9b",
    "reflection_lm": "",
    "candidate_selection_strategy": "pareto",
    "skip_perfect_score": True,
    "reflection_minibatch_size": 3,
    "perfect_score": 1.0,
    "failure_score": 0.0,
    "use_merge": True,
    "max_merge_invocations": 5,
    "seed": 0,
    "max_full_evals": None,
    "max_metric_calls": None,
    "track_stats": False,
}

# Minimal evaluation config (runner uses playbook scenarios as source of truth).
EVAL_CONFIG = {
    "scenario_source": "playbook.feature_specifications.scenarios",
    "metric": "keyword_overlap",
}
COMPILED_SPEC_PATH = Path(__file__).resolve().parent / "rag_surrealdb_dspy_demo_pipeline_compiled_spec.json"
def _load_compiled_spec(path: Path):
    try:
        with path.open("r", encoding="utf-8") as _spec_file:
            return json.load(_spec_file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Compiled spec file not found at {path}. Recompile this agent to regenerate pipeline artifacts."
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Compiled spec file is invalid JSON at {path}. Recompile this agent to regenerate pipeline artifacts."
        ) from exc


_COMPILED_SPEC = _load_compiled_spec(COMPILED_SPEC_PATH)

DSPY_ADAPTER_CONFIG = dict(_COMPILED_SPEC.get("_dspy_adapter", {}) or {})
DSPY_TOOL_CONFIG = dict((_COMPILED_SPEC.get("dspy", {}) or {}).get("tools", {}) or {})
DSPY_TOOL_NAMES = list(((_COMPILED_SPEC.get("tool_calling", {}) or {}).get("available_tools", [])) or [])
DSPY_MODULE_NAME = str(((_COMPILED_SPEC.get("reasoning", {}) or {}).get("method")) or "chain_of_thought")
DSPY_SIGNATURE_CONFIG = dict(_COMPILED_SPEC.get("_dspy_signature", {"output_mode": "simple"}) or {"output_mode": "simple"})
DSPY_ASSERTIONS_CONFIG = dict(
    _COMPILED_SPEC.get("_dspy_assertions", {"enabled": False, "mode": "fail_fast", "metric_weight": 0.3})
    or {"enabled": False, "mode": "fail_fast", "metric_weight": 0.3}
)
OUTPUT_FIELD_TYPES = {
    str(field.get("name", "output")): str(field.get("dspy_type", "str"))
    for field in list(_COMPILED_SPEC.get("output_fields", []) or [])
    if isinstance(field, dict) and field.get("name")
}


def setup_lm(model_name, api_key, temperature, max_tokens, api_base=None):
    """
    Canonical DSPy setup pattern:
        lm = dspy.LM(...)
        dspy.configure(lm=lm)
    """
    lm_kwargs = {
        "model": model_name,
        "api_key": api_key,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if api_base:
        lm_kwargs["api_base"] = api_base
    lm = dspy.LM(**lm_kwargs)
    dspy.configure(lm=lm)
    return lm


def get_optimization_config():
    """Expose subtle optimization/eval settings so users can inspect pipeline behavior."""
    return {"gepa": GEPA_CONFIG, "eval": EVAL_CONFIG}


def get_dspy_runtime_config():
    """Expose DSPy runtime config for SuperOptiX runner (adapter/tools)."""
    return {
        "module": DSPY_MODULE_NAME,
        "adapter": DSPY_ADAPTER_CONFIG,
        "signature": DSPY_SIGNATURE_CONFIG,
        "assertions": DSPY_ASSERTIONS_CONFIG,
        "tools": {"mode": DSPY_TOOL_CONFIG.get("mode", "builtin"), "names": DSPY_TOOL_NAMES},
    }


def postprocess_prediction(prediction, result, output_fields):
    """Pipeline hook delegates structured coercion to shared SuperOptiX runtime."""
    return _runtime_postprocess_prediction(
        prediction,
        result,
        output_fields,
        signature_config=DSPY_SIGNATURE_CONFIG,
        output_field_types=OUTPUT_FIELD_TYPES,
    )


def validate_prediction_result(result):
    """Pipeline hook delegates assertions to shared SuperOptiX runtime."""
    return _runtime_validate_prediction_result(
        result,
        assertions_config=DSPY_ASSERTIONS_CONFIG,
    )


def build_builtin_tools(tool_names):
    """Build DSPy-compatible built-in tools via shared SuperOptiX runtime."""
    return _runtime_build_builtin_tools(tool_names)




class RagSurrealdbDspyDemoSignature(dspy.Signature):
    """
    Role: SurrealDB RAG DSPy Analyst
    Goal: Retrieve relevant context from SurrealDB and answer clearly.
    Traits: grounded, concise, practical
    Task Instruction: Analyze the query and answer using SurrealDB retrieved context.
    """

    knowledge_query: str = dspy.InputField(desc="Query to answer using retrieved SurrealDB context.")

    retrieved_response: str = dspy.OutputField(desc="Response grounded in retrieved knowledge.")


class RagSurrealdbDspyDemoModule(dspy.Module):
    """DSPy-native program module."""

    def __init__(self):
        super().__init__()
        self.program = dspy.ChainOfThought(RagSurrealdbDspyDemoSignature)

    def forward(self, knowledge_query: str):
        return self.program(knowledge_query=knowledge_query)


def build_program() -> dspy.Module:
    """Factory used by SuperOptiX runner to execute this DSPy program."""
    return RagSurrealdbDspyDemoModule()