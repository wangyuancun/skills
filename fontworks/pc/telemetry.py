"""Telemetry is DISABLED in this build.

Upstream Punchcutter reported anonymous usage counts to PostHog (a US service).
In a SkillHub release under PIPL that creates cross-border data obligations, so
all network reporting has been removed. This module is a no-op stub kept only
for API compatibility — no data of any kind leaves the user's machine.
"""
from __future__ import annotations

SURFACE = {"name": "cli"}
_client = {"name": "", "version": ""}


def enabled():
    return False


def _send(*args, **kwargs):
    return None


def track(event, **props):
    return None


def flush(timeout=3.0):
    return None


def set_enabled(on: bool):
    return None


def set_client(name, version=""):
    _client["name"], _client["version"] = (name or "")[:60], (version or "")[:30]


def install_id():
    return ""


def studio_snippet():
    return ""


def route_of(spec: dict) -> str:
    if spec.get("mode") == "remix":
        return "open_base"
    if spec.get("mode") == "handwriting":
        return spec.get("route") or "handwriting"
    return "describe"
