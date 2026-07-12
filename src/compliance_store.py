#!/usr/bin/env python3
"""
The compliance-asset file store seam — where uploaded compliance documents' BYTES
live (ISO certs, insurance, policies, framework letters).

Mirrors the library.py provider pattern: one interface, swappable backends.
  - **LocalFileStore (now)** — writes to a gitignored dir under `src/`
    (`src/compliance_store/`), so it travels with the code like `bids.db` and is
    NEVER committed — the files are company-confidential (CLAUDE.md hard rule).
  - **SharePointStore (later)** — drops in behind the same interface when MS Graph
    lands, so the app code (api.py) never changes.
Selected via COMPLIANCE_STORE (default local_file), mirroring LIBRARY_PROVIDER.

The store owns only opaque bytes keyed by a *generated* stored-path; all metadata
(name, category, expiry, ...) lives in the `compliance_assets` table. Stored paths
are generated (uuid + a safe extension), never derived from the client filename,
so a hostile filename can't escape the store root (path traversal). Reads/deletes
re-confine every path to the root before touching disk.
"""
import os
import uuid

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_ROOT = os.path.join(_HERE, "compliance_store")

# Cap upload size so a single request can't exhaust disk (PoC-scale guard).
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB

# Extensions accepted for a compliance document. This is a sanity filter on what a
# cert/policy can be, not a security boundary on its own — stored bytes are never
# executed, and downloads are always served as an attachment (api.py).
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".png", ".jpg", ".jpeg", ".txt", ".csv",
}


def safe_ext(filename):
    """The lower-cased extension of `filename` if it's allowed, else "" (reject)."""
    ext = os.path.splitext(filename or "")[1].lower()
    return ext if ext in ALLOWED_EXTENSIONS else ""


class ComplianceStore:
    """The seam. A backend supplies save/open/delete/exists over opaque bytes."""
    name = "base"

    def save(self, data, filename):
        """Persist `data` bytes; return a stored_path handle (a string)."""
        raise NotImplementedError

    def open(self, stored_path):
        """Return the stored bytes for `stored_path`."""
        raise NotImplementedError

    def delete(self, stored_path):
        """Remove the stored file. Returns True if removed, False if absent."""
        raise NotImplementedError

    def exists(self, stored_path):
        """Whether `stored_path` currently resolves to a stored file."""
        raise NotImplementedError


class LocalFileStore(ComplianceStore):
    """Bytes on local disk under a gitignored root. Overridable root via
    COMPLIANCE_STORE_ROOT so tests can point at a temp dir."""
    name = "local_file"

    def __init__(self, root=None):
        self._root = os.path.abspath(
            root or os.environ.get("COMPLIANCE_STORE_ROOT", _DEFAULT_ROOT))

    def _abs(self, stored_path):
        """Absolute on-disk path for a stored_path, confined to the root — a
        stored_path that would escape the root (traversal) raises."""
        if not stored_path:
            raise ValueError("empty stored_path")
        p = os.path.abspath(os.path.join(self._root, stored_path))
        if os.path.commonpath([p, self._root]) != self._root:
            raise ValueError("stored_path escapes the store root")
        return p

    def save(self, data, filename):
        ext = safe_ext(filename)
        if not ext:
            raise ValueError(f"unsupported file type: {filename!r}")
        stored = uuid.uuid4().hex + ext
        os.makedirs(self._root, exist_ok=True)
        with open(self._abs(stored), "wb") as fh:
            fh.write(data)
        return stored

    def open(self, stored_path):
        with open(self._abs(stored_path), "rb") as fh:
            return fh.read()

    def delete(self, stored_path):
        try:
            os.remove(self._abs(stored_path))
            return True
        except (FileNotFoundError, ValueError):
            return False

    def exists(self, stored_path):
        try:
            return os.path.exists(self._abs(stored_path))
        except ValueError:
            return False


def get_store():
    """The active compliance store (local_file now; sharepoint later via
    COMPLIANCE_STORE, mirroring library.get_provider)."""
    key = os.environ.get("COMPLIANCE_STORE", "local_file").strip().lower()
    if key == "local_file":
        return LocalFileStore()
    # SharePointStore slots in here behind the same interface when MS Graph lands —
    # not built (no MS Graph in this environment; CLAUDE.md hard rule).
    if key == "sharepoint":
        raise RuntimeError(
            "COMPLIANCE_STORE=sharepoint is not built yet (no MS Graph access). "
            "Use local_file until SharePointStore lands.")
    raise RuntimeError(
        f"Unknown COMPLIANCE_STORE '{key}'. Valid: local_file (sharepoint planned).")
