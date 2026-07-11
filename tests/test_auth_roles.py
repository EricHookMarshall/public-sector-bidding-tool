"""Entra ID role resolution (auth.py) — the authorization rules, without tokens.

These are the pure, env-driven pieces of the auth layer: mapping a token's
`groups` claim to a role (most-privileged wins), refusing typo'd roles, and
failing closed when no role policy is configured under real auth. Token
signature/JWKS validation needs minted RSA keys and is out of scope here.
"""
import auth

G_ADMIN = "00000000-0000-0000-0000-00000000admin"
G_USER = "00000000-0000-0000-0000-000000000user"


def test_most_privileged_group_wins(monkeypatch):
    monkeypatch.setenv("AAD_GROUP_ROLE_MAP",
                       f'{{"{G_USER}": "User", "{G_ADMIN}": "Admin"}}')
    # Order must not matter — Admin outranks User either way.
    assert auth.resolve_role_from_groups([G_USER, G_ADMIN]) == "Admin"
    assert auth.resolve_role_from_groups([G_ADMIN, G_USER]) == "Admin"


def test_unknown_role_value_is_dropped(monkeypatch):
    # A typo'd role can't grant a phantom role; with no valid mapping and no
    # default configured, resolution falls through to the "User" default.
    monkeypatch.setenv("AAD_GROUP_ROLE_MAP", f'{{"{G_ADMIN}": "Superuser"}}')
    monkeypatch.delenv("AAD_DEFAULT_ROLE", raising=False)
    assert auth.resolve_role_from_groups([G_ADMIN]) == "User"


def test_unmapped_group_gets_default_role(monkeypatch):
    monkeypatch.setenv("AAD_GROUP_ROLE_MAP", f'{{"{G_ADMIN}": "Admin"}}')
    monkeypatch.setenv("AAD_DEFAULT_ROLE", "User")
    assert auth.resolve_role_from_groups(["some-unmapped-group"]) == "User"


def test_strict_membership_yields_no_role(monkeypatch):
    # Empty AAD_DEFAULT_ROLE == strict: an unmapped caller gets no role.
    monkeypatch.setenv("AAD_GROUP_ROLE_MAP", f'{{"{G_ADMIN}": "Admin"}}')
    monkeypatch.setenv("AAD_DEFAULT_ROLE", "")
    assert auth.resolve_role_from_groups(["unmapped"]) is None


def test_malformed_group_map_is_ignored(monkeypatch):
    monkeypatch.setenv("AAD_GROUP_ROLE_MAP", "{not valid json")
    monkeypatch.setenv("AAD_DEFAULT_ROLE", "User")
    assert auth.resolve_role_from_groups([G_ADMIN]) == "User"


def test_policy_fails_closed_when_unconfigured(monkeypatch):
    # No group map AND no explicit default → refuse to grant a role implicitly.
    monkeypatch.setenv("AAD_GROUP_ROLE_MAP", "")
    monkeypatch.delenv("AAD_DEFAULT_ROLE", raising=False)
    assert auth._auth_policy_error() is not None


def test_policy_ok_when_default_explicitly_set(monkeypatch):
    monkeypatch.setenv("AAD_GROUP_ROLE_MAP", "")
    monkeypatch.setenv("AAD_DEFAULT_ROLE", "")   # explicit strict choice is safe
    assert auth._auth_policy_error() is None
