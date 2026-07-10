#!/usr/bin/env python3
"""
Entra ID (Azure AD) auth for the bidding API — Azure-migration Phase C.

Clones TalentGrow's proven pattern (aadAuth.ts + devAuth.ts + groupRoleMap.ts),
in Python. One `Depends(require_auth)` guard, wired app-wide in api.py, protects
every /api/* route. It validates a real Entra **v2 access token** — JWKS
signature, issuer, audience, expiry (via PyJWT) — then resolves a role from the
token's `groups` claim. No token / invalid token → 401; wrong role → 403.

Two seams keep this buildable and verifiable locally, with **no Azure spend**:

  * LOCAL_AUTH_BYPASS=1  → skip all token checks and return a synthetic dev
    identity (default role Admin). This is TalentGrow's `local.settings.json`
    pattern: offline dev, or the current single-user PoC, runs exactly as before.
  * A self-minted RSA token against a local JWKS proves the *real* validation
    path without a live tenant (see scratchpad verify script / Phase C notes).

Two Entra security groups back the two roles: **Admin** (close to god rights
within the app — e.g. the Settings/LLM config) and **User** (an employee working
a bid through the six stages). Each group's object id maps to its role.

Divergences from TalentGrow, both because FWF's bidding-tool Entra security
groups aren't provisioned in this repo (documented, honest — not invented IDs
committed to git):
  * the group→role map is **env-driven** (AAD_GROUP_ROLE_MAP as JSON), empty by
    default — no placeholder group object IDs baked into the repo;
  * with a populated map, an authenticated caller gets AAD_DEFAULT_ROLE for an
    unmapped group. Under **real auth** (bypass off) we refuse to apply a role
    *implicitly*: you must either populate AAD_GROUP_ROLE_MAP or explicitly set
    AAD_DEFAULT_ROLE (""=strict membership; "User"=any valid token becomes a
    User). No explicit policy → fail closed (500), so a broad default is never
    silently in force on Azure. `LOCAL_AUTH_BYPASS=1` dev is unaffected.
  * a group-overage token (user in >~200 groups → Entra truncates `groups`) is
    rejected loudly under a group-mapped deployment rather than silently
    downgraded to the default role — app-role assignments are the long-term fix.

Config (all from os.environ / the git-ignored .env, like the rest of the app):
  AAD_TENANT_ID        Entra tenant GUID. Issuer + JWKS are derived from it.
  AAD_API_CLIENT_ID    This API's app-registration client id = the token audience.
  AAD_GROUP_ROLE_MAP   JSON object {"<group-object-id>": "<Role>"}. Optional.
  AAD_DEFAULT_ROLE     Role for an authenticated caller with no mapped group
                       (default "User"). Set to "" to require a mapped group.
  LOCAL_AUTH_BYPASS    "1"/"true" → offline dev shim (synthetic identity, no token).
  LOCAL_AUTH_ROLE      Role the bypass shim grants (default "Admin"). Set to
                       "User" to exercise role-gating live in the local app.
"""
import json
import logging
import os
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request

_log = logging.getLogger("bidding.auth")

# PyJWT does the crypto (RS256 via the `cryptography` extra, already installed).
# Imported lazily-tolerantly so the module still loads for the bypass path even
# if PyJWT were somehow absent — the real path raises a clear 500 instead.
try:
    import jwt
    from jwt import PyJWKClient
    try:
        # Genuine JWKS-endpoint network failures (added in newer PyJWT); a stub
        # that can't match on older versions so the except clause is harmless.
        from jwt.exceptions import PyJWKClientConnectionError
    except ImportError:  # pragma: no cover
        class PyJWKClientConnectionError(Exception):
            pass
except ImportError:  # pragma: no cover - PyJWT is a declared dependency
    jwt = None
    PyJWKClient = None

    class PyJWKClientConnectionError(Exception):
        pass


# ---- Roles ------------------------------------------------------------------
# Bidding-tool roles, most-privileged first. Two, matching the two Entra
# security groups: Admin has close to god rights within the app (e.g. changing
# LLM/Settings config); User is an employee working a bid through the six
# stages. Precedence makes the effective role deterministic when a caller is in
# both mapped groups (Entra does not guarantee `groups`-claim order).
ROLE_PRECEDENCE = {"Admin": 2, "User": 1}
VALID_ROLES = set(ROLE_PRECEDENCE)


@dataclass
class Identity:
    """The authenticated caller, resolved from a validated token (or the bypass
    shim). Mirrors TalentGrow's AuthContext."""
    role: str
    user_id: str
    display_name: str
    email: str
    via: str  # "entra" | "bypass" — provenance, for honest logging/debugging.


def _bypass_enabled() -> bool:
    return os.environ.get("LOCAL_AUTH_BYPASS", "").strip().lower() in {"1", "true", "yes"}


def _default_role() -> str:
    """AAD_DEFAULT_ROLE, defaulting to User (least privilege). Empty string → no
    default (strict: caller must be in the User or Admin group)."""
    return os.environ.get("AAD_DEFAULT_ROLE", "User").strip()


def _group_role_map() -> dict:
    """Parse AAD_GROUP_ROLE_MAP (JSON {group_id: role}). Empty/malformed → {}
    (falls back to the default role). Unknown role values are dropped so a typo
    can't grant a phantom role."""
    raw = os.environ.get("AAD_GROUP_ROLE_MAP", "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(gid): role for gid, role in parsed.items() if role in VALID_ROLES}


def _auth_policy_error() -> str | None:
    """Under real auth (bypass off), refuse to grant a role *implicitly*. Returns
    a reason string when the config is unsafe, else None. Safe iff either an
    explicit group→role map is set, OR the operator explicitly chose
    AAD_DEFAULT_ROLE (including "" for strict membership). Without one of those, a
    bare `AAD_DEFAULT_ROLE` default of "User" would let *any* valid tenant token
    into the shared bid workspace — broader than least privilege for
    client-confidential data — so we fail closed instead."""
    if _group_role_map():
        return None
    if os.environ.get("AAD_DEFAULT_ROLE") is not None:
        return None
    return ("No group-role policy configured. Set AAD_GROUP_ROLE_MAP (JSON "
            "{group_id: role}), or explicitly set AAD_DEFAULT_ROLE (\"\" for strict "
            "group membership). Refusing to grant a role implicitly under real auth.")


def _has_group_overage(claims: dict) -> bool:
    """True when Entra truncated the `groups` claim (user in >~200 groups): it
    omits `groups` and emits a `hasgroups` flag / a `_claim_names.groups` marker
    pointing at the Graph endpoint. Treated as a hard error rather than 'no
    groups', which would silently downgrade a group-mapped Admin to the default."""
    if claims.get("hasgroups"):
        return True
    claim_names = claims.get("_claim_names")
    return isinstance(claim_names, dict) and "groups" in claim_names


def resolve_role_from_groups(group_ids) -> str | None:
    """Group-object-ids → the most-privileged mapped role, or the configured
    default role, or None. Matches TalentGrow's resolveRoleFromGroups plus the
    env-driven default-role fallback for pre-groups dev."""
    role_map = _group_role_map()
    best = None
    for gid in group_ids or []:
        role = role_map.get(str(gid))
        if role and (best is None or ROLE_PRECEDENCE[role] > ROLE_PRECEDENCE[best]):
            best = role
    if best is not None:
        return best
    default = _default_role()
    return default if default in VALID_ROLES else None


# ---- JWKS / token validation ------------------------------------------------
# One cached PyJWKClient per process (it caches signing keys internally and
# refreshes on rotation). Keyed by the JWKS URL so a tenant/env change is picked
# up without a restart in tests.
_jwks_clients: dict = {}


def _jwks_client(tenant_id: str):
    url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    client = _jwks_clients.get(url)
    if client is None:
        client = PyJWKClient(url, cache_keys=True)
        _jwks_clients[url] = client
    return client


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization")
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token.strip() else None


def _validate_token(token: str, tenant_id: str, audience: str) -> dict:
    """Verify signature (JWKS), issuer, audience, expiry. Raises jwt exceptions
    on any failure — the caller turns those into a 401."""
    signing_key = _jwks_client(tenant_id).get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=audience,
        issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        options={"require": ["exp", "aud", "iss"]},
    )


def _identity_from_claims(claims: dict) -> Identity | None:
    groups = claims.get("groups")
    groups = groups if isinstance(groups, list) else []
    role = resolve_role_from_groups(groups)
    if role is None:
        return None
    email = str(claims.get("preferred_username") or claims.get("email") or "").lower()
    return Identity(
        role=role,
        user_id=str(claims.get("oid") or claims.get("sub") or ""),
        display_name=str(claims.get("name") or email),
        email=email,
        via="entra",
    )


# ---- The FastAPI dependency -------------------------------------------------
def require_auth(request: Request) -> Identity:
    """Guard every /api/* route depends on (wired app-wide in api.py). Returns
    the resolved Identity, or raises 401 (no/invalid token, or no role) / 500
    (misconfigured). FastAPI caches it per-request, so routes that want the
    identity object just re-declare `Depends(require_auth)` at no extra cost."""
    if _bypass_enabled():
        # Offline / single-user PoC shim — no token required. Defaults to Admin
        # so local dev keeps full access (incl. the Admin-gated Settings), but
        # LOCAL_AUTH_ROLE lets you run the real local app *as* a User to watch
        # role-gating live (Admin-only routes → 403) without a real tenant —
        # our stand-in for TalentGrow's SWA-CLI mock-auth role switch.
        role = os.environ.get("LOCAL_AUTH_ROLE", "Admin").strip() or "Admin"
        if role not in VALID_ROLES:
            role = "Admin"
        return Identity(
            role=role,
            user_id="local-dev",
            display_name=f"Local Dev ({role})",
            email="local-dev@localhost",
            via="bypass",
        )

    tenant_id = os.environ.get("AAD_TENANT_ID", "").strip()
    audience = os.environ.get("AAD_API_CLIENT_ID", "").strip()
    if not tenant_id or not audience:
        # Auth is required (bypass off) but not configured — fail closed, loudly.
        raise HTTPException(
            status_code=500,
            detail="Auth is enabled but AAD_TENANT_ID / AAD_API_CLIENT_ID are not set. "
                   "Set them, or set LOCAL_AUTH_BYPASS=1 for offline dev.",
        )
    policy_error = _auth_policy_error()
    if policy_error:
        # No group-role policy AND no explicit default → don't silently grant a
        # broad role; fail closed with actionable guidance.
        raise HTTPException(status_code=500, detail=policy_error)
    if jwt is None:  # pragma: no cover
        raise HTTPException(status_code=500, detail="PyJWT is not installed on the API host.")

    token = _bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated. A Microsoft Entra ID bearer token is required.")

    try:
        claims = _validate_token(token, tenant_id, audience)
    except PyJWKClientConnectionError as exc:  # JWKS endpoint unreachable — outage, not a bad token
        # Reporting a transient outage as 401 would misdiagnose every caller as
        # unauthenticated and invite credential-flailing; surface it as 503.
        _log.error("JWKS fetch failed (auth service degraded): %s", exc)
        raise HTTPException(status_code=503, detail="Auth service temporarily unavailable.") from exc
    except jwt.PyJWTError as exc:  # invalid signature / audience / issuer / expiry / malformed
        # Generic client message; the specific reason is logged server-side, not
        # leaked to the caller (token-validation internals aren't the caller's).
        _log.warning("token validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from exc

    # A group-mapped deployment must not silently downgrade an overaged user.
    if _group_role_map() and _has_group_overage(claims) and not claims.get("groups"):
        raise HTTPException(
            status_code=403,
            detail="Group membership was truncated by Entra (group overage). Configure "
                   "app-role assignments or a Graph group lookup; the token's group "
                   "claim can't be trusted for role resolution.",
        )

    identity = _identity_from_claims(claims)
    if identity is None:
        raise HTTPException(status_code=403, detail="Token is valid but grants no role for this application.")
    return identity


def require_roles(*allowed: str):
    """Dependency factory for role-gated routes: `Depends(require_roles("Admin"))`.
    401 flows through require_auth; a valid caller lacking the role → 403."""
    allowed_set = set(allowed)

    def _guard(identity: Identity = Depends(require_auth)) -> Identity:
        if identity.role not in allowed_set:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{identity.role}' is not permitted. Requires one of: {', '.join(sorted(allowed_set))}.",
            )
        return identity

    return _guard


def auth_status() -> dict:
    """Non-secret view of the auth config, for a /api/meta surfacing / the SPA to
    know whether sign-in is expected. Never returns secrets (there are none here —
    tokens are validated, not stored)."""
    return {
        "bypass": _bypass_enabled(),
        "configured": bool(os.environ.get("AAD_TENANT_ID") and os.environ.get("AAD_API_CLIENT_ID")),
        "default_role": _default_role() or None,
        "mapped_groups": len(_group_role_map()),
    }
