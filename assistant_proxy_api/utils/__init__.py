# -*- coding: utf-8 -*-
"""Настройка консоли для корректного вывода кириллицы (в т.ч. Windows)."""
import sys


def configure_stdio_utf8() -> None:
    """Переключает stdout/stderr на UTF-8, если платформа это поддерживает."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (AttributeError, ValueError, OSError):
                pass
