#!/usr/bin/env python3
"""
Auth API smoke test (stdlib only - no pip deps).

Runs: register -> login -> /me -> simulate reload via cookie-only refresh -> logout -> refresh must fail.

Usage:
  python scripts/smoke_auth.py
  python scripts/smoke_auth.py --base-url http://127.0.0.1:8000

Env (optional):
  SMOKE_ADMIN_PASSWORD   If set, verifies pedrocarneiro.dev@gmail.com (register if needed, login, /me is_admin, dev /auth/admin/check).
  SMOKE_SKIP_ADMIN=1     Skip default admin@example.com bootstrap check.

Exit codes: 0 success, 1 failure (including unreachable backend).

Requires the FastAPI backend to be running on the base URL.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar


def ok(msg: str) -> None:
    print(f"  OK  {msg}")


def fail(msg: str) -> None:
    print(f"FAIL  {msg}", file=sys.stderr)


def request_json(
    opener: urllib.request.OpenerDirector,
    method: str,
    url: str,
    *,
    data: dict | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict | list | str | None]:
    payload = json.dumps(data).encode() if data is not None else None
    h = dict(headers or {})
    if data is not None:
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=payload, headers=h, method=method)
    try:
        with opener.open(req, timeout=30) as resp:
            raw = resp.read().decode()
            ctype = resp.headers.get("Content-Type", "")
            code = resp.getcode()
    except urllib.error.HTTPError as e:
        raw = e.read().decode() if e.fp else ""
        code = e.code
        ctype = e.headers.get("Content-Type", "") if e.headers else ""

    body: dict | list | str | None
    if "application/json" in ctype.lower() and raw.strip():
        try:
            parsed = json.loads(raw)
            body = parsed if isinstance(parsed, (dict, list)) else raw
        except json.JSONDecodeError:
            body = raw
    else:
        body = raw if raw else None

    return code, body


def detail_text(body: object) -> str:
    if isinstance(body, dict):
        d = body.get("detail")
        if isinstance(d, str):
            return d
        if isinstance(d, list):
            parts: list[str] = []
            for item in d:
                if isinstance(item, dict):
                    msg = item.get("msg")
                    parts.append(str(msg) if msg else json.dumps(item, ensure_ascii=False))
                else:
                    parts.append(str(item))
            return "; ".join(parts)
    return str(body)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Auth API smoke test")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Backend base URL (default: %(default)s)",
    )
    parser.add_argument(
        "--skip-admin-verify",
        action="store_true",
        help="Skip admin@example.com bootstrap login check (e.g. ADMIN_EMAIL-only setups)",
    )
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    cookie_jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    stamp = str(int(time.time()))
    email = f"smoke_{stamp}@example.com"
    password = "SmokeTestPass123!"

    print(f"Smoke test -> {base}\n")

    # 1) Register
    code, body = request_json(opener, "POST", f"{base}/auth/register", data={"email": email, "password": password})
    if code != 201:
        fail(f"register expected 201, got {code}: {detail_text(body)}")
        return 1
    uid = body.get("id") if isinstance(body, dict) else None
    if isinstance(body, dict) and body.get("is_admin") is True:
        fail("register: normal smoke user must have is_admin=False")
        return 1
    ok(f"POST /auth/register (201{f', id={uid}' if uid is not None else ''}, is_admin=false)")
    sys.stdout.flush()

    # 2) Login (sets refresh_token cookie)
    code, body = request_json(opener, "POST", f"{base}/auth/login", data={"email": email, "password": password})
    if code != 200 or not isinstance(body, dict):
        fail(f"login expected 200 with JSON body, got {code}: {detail_text(body)}")
        return 1
    access = body.get("access_token")
    if not isinstance(access, str):
        fail("login missing access_token")
        return 1
    ok("POST /auth/login (200, cookie set)")

    # 3) /auth/me with Bearer
    code, body = request_json(
        opener,
        "GET",
        f"{base}/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    if code != 200 or not isinstance(body, dict) or body.get("email") != email:
        fail(f"GET /auth/me expected 200 for user email, got {code}: {detail_text(body)}")
        return 1
    if body.get("is_admin") is True:
        fail("GET /auth/me: normal user must have is_admin=False")
        return 1
    ok(f"GET /auth/me (200, email={email}, is_admin=false)")

    # 4) Simulate browser reload (no Bearer in "memory" - restore via cookie refresh)
    code, refresh_body = request_json(opener, "POST", f"{base}/auth/refresh")
    if code != 200 or not isinstance(refresh_body, dict):
        fail(f"POST /auth/refresh expected 200, got {code}: {detail_text(refresh_body)}")
        return 1
    access2 = refresh_body.get("access_token")
    if not isinstance(access2, str):
        fail("refresh missing access_token")
        return 1
    code, body = request_json(
        opener,
        "GET",
        f"{base}/auth/me",
        headers={"Authorization": f"Bearer {access2}"},
    )
    if code != 200:
        fail(f"GET /auth/me after refresh failed: {code}: {detail_text(body)}")
        return 1
    ok("Session restore simulation: POST /auth/refresh + GET /auth/me (both 200)")

    # 5) Logout
    code, body = request_json(opener, "POST", f"{base}/auth/logout")
    if code != 200:
        fail(f"POST /auth/logout expected 200, got {code}: {detail_text(body)}")
        return 1
    ok("POST /auth/logout (200)")

    # 6) Refresh after logout - must fail
    code, body = request_json(opener, "POST", f"{base}/auth/refresh")
    if code != 401:
        fail(f"POST /auth/refresh after logout expected 401, got {code}: {detail_text(body)}")
        return 1
    ok(f"POST /auth/refresh after logout (401 - {detail_text(body)})")

    skip_admin = args.skip_admin_verify or os.environ.get("SMOKE_SKIP_ADMIN", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if not skip_admin:
        print("\nAdmin bootstrap user (admin@example.com) ...")
        jar_ad = CookieJar()
        opener_ad = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar_ad))
        code_ad, bod_ad = request_json(
            opener_ad,
            "POST",
            f"{base}/auth/login",
            data={"email": "admin@example.com", "password": "admin123"},
        )
        if code_ad != 200 or not isinstance(bod_ad, dict):
            fail(
                f"admin login expected 200, got {code_ad}: {detail_text(bod_ad)} "
                "(use --skip-admin-verify if you only use ADMIN_EMAIL)"
            )
            return 1
        tok_ad = bod_ad.get("access_token")
        if not isinstance(tok_ad, str):
            fail("admin login missing access_token")
            return 1
        code_ad, bod_ad = request_json(
            opener_ad,
            "GET",
            f"{base}/auth/me",
            headers={"Authorization": f"Bearer {tok_ad}"},
        )
        if code_ad != 200 or not isinstance(bod_ad, dict):
            fail(f"admin GET /auth/me failed: {code_ad}: {detail_text(bod_ad)}")
            return 1
        if bod_ad.get("is_admin") is not True:
            fail(f"admin user must have is_admin=True on /auth/me, got {bod_ad.get('is_admin')}")
            return 1
        ok("admin login + GET /auth/me (is_admin=true)")

    custom_pw = os.environ.get("SMOKE_ADMIN_PASSWORD", "").strip()
    if custom_pw:
        print("\nCustom admin (ADMIN_EMAIL / pedrocarneiro.dev@gmail.com) ...")
        custom_email = "pedrocarneiro.dev@gmail.com"
        jar_c = CookieJar()
        opener_c = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar_c))
        code_c, bod_c = request_json(
            opener_c,
            "POST",
            f"{base}/auth/register",
            data={"email": custom_email, "password": custom_pw},
        )
        if code_c not in (201, 400):
            fail(f"custom admin register expected 201 or 400, got {code_c}: {detail_text(bod_c)}")
            return 1
        if code_c == 201:
            ok("POST /auth/register (custom admin email, is_admin expected true)")
        else:
            ok("POST /auth/register (400 expected if user exists)")
        code_c, bod_c = request_json(
            opener_c,
            "POST",
            f"{base}/auth/login",
            data={"email": custom_email, "password": custom_pw},
        )
        if code_c != 200 or not isinstance(bod_c, dict):
            fail(f"custom admin login failed {code_c}: {detail_text(bod_c)}")
            return 1
        tok_c = bod_c.get("access_token")
        if not isinstance(tok_c, str):
            fail("custom admin login missing access_token")
            return 1
        code_c, bod_c = request_json(
            opener_c,
            "GET",
            f"{base}/auth/me",
            headers={"Authorization": f"Bearer {tok_c}"},
        )
        if code_c != 200 or not isinstance(bod_c, dict) or bod_c.get("email") != custom_email:
            fail(f"custom admin GET /auth/me failed {code_c}: {detail_text(bod_c)}")
            return 1
        if bod_c.get("is_admin") is not True:
            fail("custom admin must have is_admin=true on /auth/me")
            return 1
        ok("custom admin GET /auth/me (is_admin=true)")
        code_c, bod_c = request_json(
            opener_c,
            "GET",
            f"{base}/auth/admin/check",
            headers={"Authorization": f"Bearer {tok_c}"},
        )
        if code_c == 200:
            if not isinstance(bod_c, dict) or bod_c.get("status") != "ok" or bod_c.get("admin") is not True:
                fail(f"GET /auth/admin/check unexpected body: {bod_c}")
                return 1
            ok("GET /auth/admin/check (200, dev route)")
        elif code_c == 404:
            ok("GET /auth/admin/check (404, production or non-dev)")
        else:
            fail(f"GET /auth/admin/check expected 200 or 404, got {code_c}: {detail_text(bod_c)}")
            return 1
    else:
        print("\n  (Set SMOKE_ADMIN_PASSWORD to verify pedrocarneiro.dev@gmail.com admin flow.)")

    print("\nALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        fail(f"cannot reach backend ({reason!r}). Is the server running?")
        raise SystemExit(1) from e
