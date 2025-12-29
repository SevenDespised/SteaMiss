from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    *,
    log_dir: str | os.PathLike[str] = os.path.join("config", "logs"),
    level: int = logging.INFO,
    app_log_name: str = "app.log",
    error_log_name: str = "error.log",
    also_console: bool = False,
) -> Path:
    """Initialize stdlib logging.

    - Writes general logs to app.log
    - Writes ERROR+ logs (with tracebacks) to error.log

    Returns:
        Path to the log directory.
    """

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()

    # Idempotency: don't add duplicate handlers if setup_logging is called multiple times.
    if getattr(root, "_steamiss_logging_configured", False):
        return log_path

    root.setLevel(level)

    fmt = (
        "%(asctime)s | %(levelname)s | %(name)s | %(threadName)s | "
        "%(filename)s:%(lineno)d | %(message)s"
    )
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    app_handler = RotatingFileHandler(
        filename=str(log_path / app_log_name),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setLevel(level)
    app_handler.setFormatter(formatter)

    err_handler = RotatingFileHandler(
        filename=str(log_path / error_log_name),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(formatter)

    root.addHandler(app_handler)
    root.addHandler(err_handler)

    if also_console:
        console = logging.StreamHandler(stream=sys.stderr)
        console.setLevel(level)
        console.setFormatter(formatter)
        root.addHandler(console)

    setattr(root, "_steamiss_logging_configured", True)
    return log_path


def install_global_exception_hooks(logger: Optional[logging.Logger] = None) -> None:
    """Install sys/threading exception hooks to log uncaught exceptions."""

    log = logger or logging.getLogger("steamiss.excepthook")

    def _sys_hook(exc_type, exc, tb):
        if exc_type is KeyboardInterrupt:
            sys.__excepthook__(exc_type, exc, tb)
            return
        log.critical("Unhandled exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = _sys_hook

    try:
        import threading

        def _thread_hook(args):
            log.critical(
                "Unhandled exception in thread %s",
                getattr(args, "thread", None),
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )

        threading.excepthook = _thread_hook  # type: ignore[attr-defined]
    except Exception:
        log.exception("Failed to install threading.excepthook")


__all__ = ["setup_logging", "install_global_exception_hooks"]
