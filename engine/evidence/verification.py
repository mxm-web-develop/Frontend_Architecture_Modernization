from __future__ import annotations
from pathlib import Path
import json
import hashlib
import yaml

from engine.runtime_capture import validate_runtime_manifest

def resolve_ref(repo: Path, ref: str | Path) -> Path:
    p = Path(ref)
    return p.resolve() if p.is_absolute() else (repo / p).resolve()

def rel_ref(repo: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo.resolve())).replace("\\", "/")
    except Exception:
        return str(path.resolve())

def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def validate_command_evidence(repo: Path, ref: str, domain: str, gate: str) -> list[str]:
    errors = []
    path = resolve_ref(repo, ref)
    if not path.exists():
        return [f"{gate} evidence missing: {ref}"]
    try:
        data = _load_json(path)
    except Exception as exc:
        return [f"{gate} evidence is not valid JSON: {ref}: {exc}"]
    if data.get("evidence_type") != "command-run":
        errors.append(f"{gate} evidence {ref} must have evidence_type=command-run")
    if data.get("domain") != domain:
        errors.append(f"{gate} evidence {ref} domain mismatch: {data.get('domain')} != {domain}")
    if data.get("gate") != gate:
        errors.append(f"{gate} evidence {ref} gate mismatch: {data.get('gate')}")
    if data.get("status") != "PASS" or data.get("exit_code") != 0:
        errors.append(f"{gate} evidence {ref} is not a successful command run")
    for key in ("command", "started_at", "ended_at", "commit"):
        if not data.get(key):
            errors.append(f"{gate} evidence {ref} missing {key}")
    stdout_ref = data.get("stdout")
    stderr_ref = data.get("stderr")
    if stdout_ref:
        stdout_path = resolve_ref(repo, stdout_ref)
        if not stdout_path.exists():
            errors.append(f"{gate} evidence stdout missing: {stdout_ref}")
        elif data.get("stdout_sha256") and file_sha256(stdout_path) != data.get("stdout_sha256"):
            errors.append(f"{gate} evidence stdout hash mismatch: {stdout_ref}")
    if stderr_ref:
        stderr_path = resolve_ref(repo, stderr_ref)
        if not stderr_path.exists():
            errors.append(f"{gate} evidence stderr missing: {stderr_ref}")
        elif data.get("stderr_sha256") and file_sha256(stderr_path) != data.get("stderr_sha256"):
            errors.append(f"{gate} evidence stderr hash mismatch: {stderr_ref}")
    return errors

def validate_visual_result(repo: Path, ref: str, domain_dir: Path) -> list[str]:
    errors = []
    result_path = resolve_ref(repo, ref)
    if not result_path.exists():
        return [f"visual result missing: {ref}"]
    try:
        result = _load_json(result_path)
    except Exception as exc:
        return [f"visual result is not valid JSON: {ref}: {exc}"]

    manifest_path = domain_dir / "visual-manifest.json"
    if not manifest_path.exists():
        return [f"visual-manifest.json missing: {manifest_path}"]
    try:
        manifest = _load_json(manifest_path)
    except Exception as exc:
        return [f"visual-manifest.json invalid: {exc}"]

    results = {x.get("id"): x for x in result.get("results", []) if x.get("id")}
    required = [
        x for x in manifest.get("scenarios", [])
        if x.get("policy") == "STRICT_PRESERVE" or x.get("status") == "PASS"
    ]

    if not result.get("generated_at"):
        errors.append("visual result missing generated_at")
    if not result.get("environment"):
        errors.append("visual result missing environment")

    for scenario in required:
        sid = scenario.get("id")
        if not sid:
            errors.append("visual manifest contains scenario without id")
            continue
        actual = results.get(sid)
        if not actual:
            errors.append(f"visual result missing scenario: {sid}")
            continue
        if actual.get("status") != "PASS":
            errors.append(f"visual scenario {sid} is not PASS in result.json")
        # v1.2.2 harness records image refs; older results can still be derived from result directory.
        refs = {
            "legacy": actual.get("legacy_image") or f"legacy/{sid}.png",
            "target": actual.get("target_image") or f"target/{sid}.png",
            "diff": actual.get("diff_image") or f"diff/{sid}.png",
        }
        for kind, image_ref in refs.items():
            image_path = Path(image_ref)
            if not image_path.is_absolute():
                image_path = (result_path.parent / image_path).resolve()
            if not image_path.exists():
                errors.append(f"visual scenario {sid} {kind} image missing: {image_ref}")
                continue
            try:
                if image_path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                    errors.append(f"visual scenario {sid} {kind} is not a PNG: {image_ref}")
            except Exception as exc:
                errors.append(f"visual scenario {sid} {kind} cannot be read: {image_ref}: {exc}")
            expected_hash = actual.get(f"{kind}_sha256")
            if not expected_hash:
                errors.append(f"visual scenario {sid} missing {kind}_sha256")
            elif file_sha256(image_path) != expected_hash:
                errors.append(f"visual scenario {sid} {kind} hash mismatch")
        if actual.get("mismatch_pixels") is None:
            errors.append(f"visual scenario {sid} missing mismatch_pixels")
        if actual.get("ratio") is None:
            errors.append(f"visual scenario {sid} missing ratio")
    return errors


def required_command_keys(repo: Path, gate: str) -> list[str]:
    path = repo / "governance" / "quality-gates.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    gate_cfg = ((data.get("gates") or {}).get(gate) or {})
    if isinstance(gate_cfg, str):
        return []
    evidence = gate_cfg.get("evidence") or {}
    keys = evidence.get("required_command_keys") or []
    return [str(x) for x in keys]


def command_evidence_key(repo: Path, ref: str):
    path = resolve_ref(repo, ref)
    if not path.exists():
        return None
    try:
        data = _load_json(path)
    except Exception:
        return None
    return data.get("command_key")


def validate_gate_evidence(repo: Path, domain: str, status: dict, gate: str) -> list[str]:
    value = (status.get("gates") or {}).get(gate)
    if value not in {"PASS", "WAIVED", "NOT_APPLICABLE"}:
        return []
    if value in {"WAIVED", "NOT_APPLICABLE"}:
        reasons = status.get("gate_reasons") or {}
        if not reasons.get(gate):
            return [f"{domain}: gate {gate}={value} requires a recorded reason"]
        return []

    refs = (status.get("gate_evidence") or {}).get(gate) or []
    if isinstance(refs, str):
        refs = [refs]
    if not refs:
        return [f"{domain}: gate {gate}=PASS requires evidence"]

    domain_dir = repo / "migration" / "domains" / domain
    errors = []
    if gate == "visual":
        for ref in refs:
            errors.extend(validate_visual_result(repo, ref, domain_dir))
    else:
        for ref in refs:
            errors.extend(validate_command_evidence(repo, ref, domain, gate))
            # === v1.6 P1：live-runtime-snapshot / live-runtime-flow 证据也可挂在 functional / architecture / traceability 门下 ===
            try:
                data = _load_json(resolve_ref(repo, ref))
                et = (data or {}).get("evidence_type")
            except Exception:
                et = None
            if et in {"live-runtime-snapshot", "live-runtime-flow"}:
                errors.extend(validate_runtime_manifest(repo, resolve_ref(repo, ref)))
        required_keys = required_command_keys(repo, gate)
        if required_keys:
            present = {command_evidence_key(repo, ref) for ref in refs}
            missing = [key for key in required_keys if key not in present]
            if missing:
                errors.append(f"{domain}: gate {gate}=PASS missing required command evidence keys: {missing}")
    return errors

def validate_all_passed_gate_evidence(repo: Path, domain: str, status: dict) -> list[str]:
    errors = []
    for gate in ("functional", "visual", "architecture", "traceability"):
        errors.extend(validate_gate_evidence(repo, domain, status, gate))
    return errors
