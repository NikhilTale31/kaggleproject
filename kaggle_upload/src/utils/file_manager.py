import json
import os
from datetime import datetime
from typing import Any, Optional


OUTPUTS_DIR = os.path.join("outputs")
FINDINGS_DIR = os.path.join(OUTPUTS_DIR, "findings")
LOGS_DIR = os.path.join(OUTPUTS_DIR, "logs")
REPORTS_DIR = os.path.join(OUTPUTS_DIR, "reports")
SUBMISSIONS_DIR = os.path.join(OUTPUTS_DIR, "submissions")

DATA_DIR = "data"
TEMPLATES_DIR = os.path.join("src", "templates")


def _mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def ensure_dirs(
    outputs_dir: str = OUTPUTS_DIR,
    findings_dir: str = FINDINGS_DIR,
    logs_dir: str = LOGS_DIR,
    reports_dir: str = REPORTS_DIR,
    submissions_dir: str = SUBMISSIONS_DIR,
) -> None:
    """
    Ensure the standard repository directory structure exists.
    Safe to call multiple times.
    """
    _mkdir(outputs_dir)
    _mkdir(findings_dir)
    _mkdir(logs_dir)
    _mkdir(reports_dir)
    _mkdir(submissions_dir)


def read_json(path: str, default: Optional[Any] = None) -> Any:
    """
    Read a JSON file and return the parsed object.
    If the file doesn't exist and default is provided, return default.
    """
    if not os.path.isfile(path):
        if default is not None:
            return default
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: Any, indent: int = 2) -> None:
    """
    Write an object as pretty JSON to the given path, creating parent dirs if needed.
    """
    parent = os.path.dirname(path)
    if parent:
        _mkdir(parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def timestamped_path(base_dir: str, prefix: str, ext: str = "json", utc: bool = True) -> str:
    """
    Create a timestamped filename path under base_dir with given prefix and extension.
    Example: timestamped_path('outputs/findings', 'scan', 'json') ->
             outputs/findings/scan-20240521-153045Z.json
    """
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%SZ") if utc else datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{prefix}-{ts}.{ext.lstrip('.')}"
    return os.path.join(base_dir, filename)


__all__ = [
    "ensure_dirs",
    "read_json",
    "write_json",
    "timestamped_path",
    "OUTPUTS_DIR",
    "FINDINGS_DIR",
    "LOGS_DIR",
    "REPORTS_DIR",
    "SUBMISSIONS_DIR",
    "DATA_DIR",
    "TEMPLATES_DIR",
]
