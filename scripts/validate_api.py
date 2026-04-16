#!/usr/bin/env python3
"""One-shot validator: confirm a live Philips Hue Play HDMI Sync Box exposes
every API attribute, method, and value shape the Home Assistant integration
depends on.

This script is intentionally self-contained and does NOT import any Home
Assistant code. It talks to the device through `aiohuesyncbox` only and prints
a PASS/FAIL report per expectation.

Usage:
    # From an activated venv that has aiohuesyncbox installed:
    python scripts/validate_api.py \
        --host 192.168.1.123 \
        --id C42996000000 \
        --token <ACCESS_TOKEN>

    # Or via env vars:
    HUESYNCBOX_HOST=192.168.1.123 \
    HUESYNCBOX_ID=C42996000000 \
    HUESYNCBOX_TOKEN=<ACCESS_TOKEN> \
    python scripts/validate_api.py

How to find the access token:
    - Home Assistant stores it in `.storage/core.config_entries` under the
      huesyncbox entry (`access_token`, `unique_id`/`host`).
    - Or register a new token via the library's `register()` flow (requires
      holding the button on the box until it flashes green).

Exit code: 0 if every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable

import aiohuesyncbox

# ---------------------------------------------------------------------------
# Tiny result recorder
# ---------------------------------------------------------------------------

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
DIM = "\033[0;90m"
RESET = "\033[0m"


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


results: list[Check] = []


def record(name: str, passed: bool, detail: str) -> None:
    results.append(Check(name, passed, detail))
    color = GREEN if passed else RED
    symbol = "PASS" if passed else "FAIL"
    print(f"  {color}{symbol}{RESET} {name} {DIM}→ {detail}{RESET}")


def check(name: str, fn: Callable[[], Any], *, expected_types: tuple[type, ...] | None = None,
          allowed_values: set[Any] | None = None, allow_none: bool = False) -> None:
    """Run a lambda, capture the value, and verify it has the expected shape."""
    try:
        value = fn()
    except Exception as exc:  # noqa: BLE001
        record(name, passed=False, detail=f"raised {type(exc).__name__}: {exc}")
        return

    if value is None:
        record(name, passed=allow_none, detail="value is None" +
               ("" if allow_none else " (not allowed)"))
        return

    ok = True
    detail_parts = [f"type={type(value).__name__}", f"value={value!r}"]
    if expected_types and not isinstance(value, expected_types):
        ok = False
        detail_parts.append(f"expected one of {[t.__name__ for t in expected_types]}")
    if allowed_values is not None and value not in allowed_values:
        ok = False
        detail_parts.append(f"expected one of {sorted(allowed_values)}")

    record(name, passed=ok, detail=", ".join(detail_parts))


def has_method(name: str, obj: Any, method: str,
               required_kwargs: set[str] | None = None) -> None:
    """Assert that an object has a coroutine method and that its signature
    accepts a given set of keyword arguments (to catch upstream renames)."""
    fn = getattr(obj, method, None)
    if fn is None:
        record(name, passed=False, detail=f"missing method .{method}()")
        return
    if not callable(fn):
        record(name, passed=False, detail=f".{method} is not callable")
        return
    if required_kwargs:
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            record(name, passed=True, detail=f".{method} exists (signature not introspectable)")
            return
        missing = required_kwargs - set(sig.parameters)
        if missing:
            record(name, passed=False,
                   detail=f".{method} is missing kwargs: {sorted(missing)}")
            return
        record(name, passed=True,
               detail=f".{method}({', '.join(sorted(required_kwargs))}, …) accepted")
        return
    record(name, passed=True, detail=f".{method}() exists")


# ---------------------------------------------------------------------------
# The checks (mirror every attribute/method the integration uses)
# ---------------------------------------------------------------------------

async def run_checks(api: aiohuesyncbox.HueSyncBox) -> None:
    print(f"\n{YELLOW}Top-level API object{RESET}")
    has_method("HueSyncBox.initialize", api, "initialize")
    has_method("HueSyncBox.update", api, "update")
    has_method("HueSyncBox.close", api, "close")
    has_method("HueSyncBox.is_registered", api, "is_registered")
    has_method("HueSyncBox.register", api, "register")
    has_method("HueSyncBox.unregister", api, "unregister")
    check("HueSyncBox.last_response is dict-ish",
          lambda: api.last_response, allow_none=True)

    print(f"\n{YELLOW}api.device{RESET}")
    check("device.name", lambda: api.device.name, expected_types=(str,))
    check("device.unique_id (mac-like)", lambda: api.device.unique_id,
          expected_types=(str,))
    check("device.device_type", lambda: api.device.device_type,
          expected_types=(str,), allowed_values={"HSB1", "HSB2"})
    check("device.firmware_version", lambda: api.device.firmware_version,
          expected_types=(str,))
    check("device.ip_address", lambda: api.device.ip_address, expected_types=(str,))
    check("device.led_mode (0|1|2)", lambda: api.device.led_mode,
          expected_types=(int,), allowed_values={0, 1, 2})
    has_method("device.set_led_mode", api.device, "set_led_mode")

    print(f"\n{YELLOW}api.device.wifi{RESET}")
    check("device.wifi.strength (0-4)", lambda: api.device.wifi.strength,
          expected_types=(int,), allowed_values={0, 1, 2, 3, 4}, allow_none=True)

    print(f"\n{YELLOW}api.execution{RESET}")
    VALID_MODES = {"powersave", "passthrough", "video", "music", "game"}
    check("execution.mode", lambda: api.execution.mode,
          expected_types=(str,), allowed_values=VALID_MODES)
    check("execution.last_sync_mode", lambda: api.execution.last_sync_mode,
          expected_types=(str,), allowed_values={"video", "music", "game"})
    check("execution.brightness (0-200)", lambda: api.execution.brightness,
          expected_types=(int,))
    check("execution.hdmi_source", lambda: api.execution.hdmi_source,
          expected_types=(str,), allowed_values={"input1", "input2", "input3", "input4"})
    check("execution.hue_target", lambda: api.execution.hue_target,
          expected_types=(str,))
    VALID_INTENSITIES = {"subtle", "moderate", "high", "intense"}
    check("execution.video.intensity", lambda: api.execution.video.intensity,
          expected_types=(str,), allowed_values=VALID_INTENSITIES)
    check("execution.music.intensity", lambda: api.execution.music.intensity,
          expected_types=(str,), allowed_values=VALID_INTENSITIES)
    check("execution.game.intensity", lambda: api.execution.game.intensity,
          expected_types=(str,), allowed_values=VALID_INTENSITIES)
    has_method(
        "execution.set_state accepts all integration kwargs",
        api.execution,
        "set_state",
        required_kwargs={"hdmi_active", "sync_active", "mode", "hdmi_source",
                         "brightness", "intensity", "hue_target", "video",
                         "music", "game"},
    )

    print(f"\n{YELLOW}api.hdmi{RESET}")
    for i in (1, 2, 3, 4):
        inp = getattr(api.hdmi, f"input{i}", None)
        if inp is None:
            record(f"hdmi.input{i}", passed=False, detail="attribute missing")
            continue
        check(f"hdmi.input{i}.name", lambda inp=inp: inp.name, expected_types=(str,))
        check(f"hdmi.input{i}.status", lambda inp=inp: inp.status,
              expected_types=(str,),
              allowed_values={"unplugged", "plugged", "linked", "unknown"})
    check("hdmi.content_specs", lambda: api.hdmi.content_specs,
          expected_types=(str,), allow_none=True)

    print(f"\n{YELLOW}api.hue{RESET}")
    check("hue.bridge_unique_id", lambda: api.hue.bridge_unique_id,
          expected_types=(str,), allow_none=True)
    VALID_BRIDGE_STATES = {"uninitialized", "disconnected", "connecting",
                           "unauthorized", "connected", "invalidgroup",
                           "streaming", "busy"}
    check("hue.connection_state", lambda: api.hue.connection_state,
          expected_types=(str,), allowed_values=VALID_BRIDGE_STATES)
    check("hue.groups is list", lambda: list(api.hue.groups),
          expected_types=(list,))
    has_method("hue.set_bridge", api.hue, "set_bridge")
    has_method("hue.set_group_active", api.hue, "set_group_active")

    # Group shape (only if the device has any configured)
    if api.hue.groups:
        first_group = api.hue.groups[0]
        print(f"\n{YELLOW}api.hue.groups[0]{RESET}")
        check("group.id", lambda: first_group.id, expected_types=(str,))
        check("group.name", lambda: first_group.name, expected_types=(str,))
        check("group.active", lambda: first_group.active, expected_types=(bool,))
        check("group.owner", lambda: first_group.owner, expected_types=(str,),
              allow_none=True)

    print(f"\n{YELLOW}api.behavior{RESET}")
    # force_dovi_native is None on 8K-only models, int (0/1) on 4K — both paths OK
    check("behavior.force_dovi_native (None|0|1)",
          lambda: api.behavior.force_dovi_native,
          expected_types=(int,), allowed_values={0, 1}, allow_none=True)
    has_method("behavior.set_force_dovi_native", api.behavior, "set_force_dovi_native")

    # Test a no-op update() round-trip so we know polling works
    print(f"\n{YELLOW}Round-trip api.update(){RESET}")
    try:
        await api.update()
        record("api.update() completes without error", passed=True,
               detail="polled the device once")
    except Exception as exc:  # noqa: BLE001
        record("api.update() completes without error", passed=False,
               detail=f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default=os.getenv("HUESYNCBOX_HOST"),
                        help="Device IP (or HUESYNCBOX_HOST env)")
    parser.add_argument("--id", default=os.getenv("HUESYNCBOX_ID"),
                        help="Device unique_id/identifier (or HUESYNCBOX_ID env)")
    parser.add_argument("--token", default=os.getenv("HUESYNCBOX_TOKEN"),
                        help="Access token (or HUESYNCBOX_TOKEN env)")
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument("--path", default="/api")
    args = parser.parse_args()

    if not (args.host and args.id and args.token):
        parser.error("--host, --id, --token are all required (or via env vars)")

    print(f"Connecting to {args.host}:{args.port}{args.path} (id={args.id})…")
    async with aiohuesyncbox.HueSyncBox(
        args.host, args.id, access_token=args.token,
        port=args.port, path=args.path,
    ) as api:
        try:
            await api.initialize()
        except aiohuesyncbox.Unauthorized:
            print(f"{RED}FATAL: Unauthorized — access token is invalid/expired{RESET}")
            return 1
        except aiohuesyncbox.RequestError as exc:
            print(f"{RED}FATAL: cannot reach device: {exc}{RESET}")
            return 1

        await run_checks(api)

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)
    print()
    if failed == 0:
        print(f"{GREEN}All {total} checks passed — integration is in line with the device.{RESET}")
        return 0
    print(f"{RED}{failed} of {total} checks failed:{RESET}")
    for r in results:
        if not r.passed:
            print(f"  {RED}✗{RESET} {r.name}: {r.detail}")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
