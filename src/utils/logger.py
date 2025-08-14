import logging
import os
import sys
from datetime import datetime
from glob import glob
from typing import Optional, Tuple


_DEFAULT_LOG_DIR = os.path.join("outputs", "logs")
_RUN_TS = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
_LOG_FILE_BASENAME = f"run-{_RUN_TS}.log"


def _ensure_dir(path: str) -> None:
    """
    Ensure a directory exists.
    """
    os.makedirs(path, exist_ok=True)


def _build_file_handler(log_dir: str, level: int) -> logging.FileHandler:
    """
    Create a rotating-like file handler (timestamped per run).
    """
    _ensure_dir(log_dir)
    file_path = os.path.join(log_dir, _LOG_FILE_BASENAME)
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(_default_formatter())
    return fh


def _build_stream_handler(level: int) -> logging.StreamHandler:
    """
    Create a stdout stream handler.
    """
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setLevel(level)
    sh.setFormatter(_default_formatter(color=False))
    return sh


def _default_formatter(color: bool = False) -> logging.Formatter:
    """
    Construct a default formatter for structured logs.
    """
    # Keeping format simple and parseable
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    return logging.Formatter(fmt=fmt, datefmt=datefmt)


def get_logger(name: str = "ai-redteaming", level: int = logging.INFO, log_dir: Optional[str] = None) -> logging.Logger:
    """
    Return a configured logger that logs to both stdout and a file in outputs/logs.

    - Creates outputs/logs if it doesn't exist.
    - Avoids adding duplicate handlers when called multiple times.
    - Uses a per-run timestamped log file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Only configure once per process for this logger name
    if not getattr(logger, "_ai_rt_configured", False):
        # Avoid noisy propagation to root
        logger.propagate = False

        target_log_dir = log_dir or _DEFAULT_LOG_DIR

        # Stream handler (stdout)
        sh = _build_stream_handler(level)
        logger.addHandler(sh)

        # File handler
        fh = _build_file_handler(target_log_dir, level)
        logger.addHandler(fh)

        # Mark as configured
        setattr(logger, "_ai_rt_configured", True)

        logger.debug(f"Logger configured. Level={logging.getLevelName(level)} File={os.path.join(target_log_dir, _LOG_FILE_BASENAME)}")

    return logger


def log_exception(logger: logging.Logger, message: str, exc: BaseException) -> None:
    """
    Convenience to log exception with traceback.
    """
    logger.error(f"{message}: {exc}", exc_info=True)


def _parse_log_line(line: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Attempt to parse a log line into (timestamp, level, name, message).
    Returns (None, None, None, None) if it doesn't match expected pattern.
    Expected format: "YYYY-MM-DD HH:MM:SS | LEVEL | name | message"
    """
    try:
        parts = [p.strip() for p in line.split("|", 3)]
        if len(parts) != 4:
            return None, None, None, None
        ts, level, name, msg = parts
        # Basic sanity check on timestamp and level
        if len(ts) < 19 or len(level) == 0 or len(name) == 0:
            return None, None, None, None
        return ts, level, name, msg
    except Exception:
        return None, None, None, None


def show_summary(log_dir: str = _DEFAULT_LOG_DIR, limit: int = 5) -> None:
    """
    Print a concise summary of logs in the given directory:
      - Total files and lines processed
      - Counts by level
      - Last N lines from the latest log file

    This is used by:
      python -c "from src.utils.logger import show_summary; show_summary()"
    """
    if not os.path.isdir(log_dir):
        print(f"[logger] No log directory found at {log_dir}")
        return

    log_files = sorted(glob(os.path.join(log_dir, "run-*.log")))
    if not log_files:
        print(f"[logger] No log files found in {log_dir}")
        return

    counts = {
        "DEBUG": 0,
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "CRITICAL": 0,
        "OTHER": 0,
    }
    total_lines = 0

    for fp in log_files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    total_lines += 1
                    _, lvl, _, _ = _parse_log_line(line)
                    if lvl in counts:
                        counts[lvl] += 1
                    else:
                        counts["OTHER"] += 1
        except Exception as e:
            print(f"[logger] Failed to read {fp}: {e}")

    latest = log_files[-1]
    tail_lines = []
    try:
        with open(latest, "r", encoding="utf-8") as f:
            # read tail efficiently
            f.seek(0, os.SEEK_END)
            filesize = f.tell()
            block = 1024
            data = ""
            while len(tail_lines) <= limit and filesize > 0:
                read_size = min(block, filesize)
                f.seek(filesize - read_size, os.SEEK_SET)
                chunk = f.read(read_size)
                data = chunk + data
                lines = data.splitlines()
                tail_lines = lines[-limit - 1 :]
                filesize -= read_size
            if not tail_lines:
                tail_lines = data.splitlines()[-limit:]
    except Exception as e:
        print(f"[logger] Failed to read tail of {latest}: {e}")

    print("==== AI Red-teaming Logs Summary ====")
    print(f"Directory: {log_dir}")
    print(f"Files: {len(log_files)}  Lines: {total_lines}")
    print("By Level:")
    for lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OTHER"]:
        print(f"  {lvl:<8} {counts[lvl]}")
    print(f"Latest file: {latest}")
    print(f"Last {limit} lines:")
    for ln in tail_lines[-limit:]:
        print(f"  {ln}")


__all__ = [
    "get_logger",
    "show_summary",
    "log_exception",
]
