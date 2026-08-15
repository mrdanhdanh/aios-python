"""TASK-040 — Security & Data Isolation (E6).

Implements three controls (PLAN §8 E6):
- ``CredentialBroker`` (INV-024): credentials are tenant/project/capability
  scoped, short-lived, and only resolved INSIDE the authorized scope. Agent/Tool
  never holds the raw secret — it receives a scoped, time-limited token.
- ``NetworkPolicy`` engine: default-deny; only explicitly allowed hosts open.
- ``SandboxBoundary`` (INV-028): untrusted tool execution MUST run under a
  sandbox profile; bypass is rejected fail-closed.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

from .contracts import CredentialRef, NetworkPolicy, SandboxProfile


class CredentialError(Exception):
    """Raised on credential isolation violations (INV-024)."""


class SandboxBypassError(Exception):
    """Raised when an untrusted tool skips the sandbox (INV-028)."""


class CredentialBroker:
    """Scoped, short-lived credential resolution (INV-024).

    Stores only ``secret_ref`` (never raw secrets in the contract). Resolution
    is gated by tenant/project/capability scope; cross-scope resolution is
    denied. A ``resolver`` injectable turns a ``secret_ref`` into a token.
    """

    def __init__(
        self,
        resolver: Callable[[str], str] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._resolver = resolver or (lambda ref: f"tok:{ref}")
        self._clock = clock or time.monotonic
        self._lock = threading.RLock()
        self._creds: dict[str, CredentialRef] = {}

    def register(self, cred: CredentialRef) -> None:
        with self._lock:
            self._creds[cred.id] = cred

    def _assert_scope(self, cred: CredentialRef, requester_tenant: str,
                      requester_project: str | None, capability: str) -> None:
        if cred.tenant_id != requester_tenant:
            raise CredentialError(
                f"INV-024: tenant {requester_tenant!r} cannot resolve credential "
                f"of tenant {cred.tenant_id!r}"
            )
        if cred.project_id is not None and cred.project_id != requester_project:
            raise CredentialError(
                f"INV-024: project {requester_project!r} cannot resolve credential "
                f"of project {cred.project_id!r}"
            )
        if cred.capability != capability:
            raise CredentialError(
                f"INV-024: capability {capability!r} cannot use credential "
                f"scoped to {cred.capability!r}"
            )

    def resolve(
        self,
        credential_id: str,
        requester_tenant: str,
        capability: str,
        requester_project: str | None = None,
    ) -> str:
        with self._lock:
            if credential_id not in self._creds:
                raise CredentialError(f"unknown credential {credential_id!r}")
            cred = self._creds[credential_id]
        self._assert_scope(cred, requester_tenant, requester_project, capability)
        if cred.expires_at is not None and cred.expires_at <= self._clock():
            raise CredentialError(f"credential {credential_id!r} expired")
        # Returns a scoped, short-lived token — never the raw secret.
        return self._resolver(cred.secret_ref or credential_id)


class NetworkPolicyEngine:
    """Default-deny network policy engine (PLAN §8 E6)."""

    def __init__(self, policy: NetworkPolicy | None = None) -> None:
        self.policy = policy or NetworkPolicy()

    def allow(self, host: str) -> bool:
        # Explicit allow wins; explicit deny always blocks (fail-closed).
        if host in self.policy.deny:
            return False
        if host in self.policy.allow:
            return True
        return False  # default-deny

    def check(self, host: str) -> None:
        if not self.allow(host):
            raise CredentialError(
                f"network policy denies {host!r} (default-deny)"
            )


class SandboxBoundary:
    """Enforces sandbox requirement for untrusted execution (INV-028)."""

    def __init__(self, profiles: dict[str, SandboxProfile] | None = None) -> None:
        self._profiles = dict(profiles or {})

    def register_profile(self, name: str, profile: SandboxProfile) -> None:
        self._profiles[name] = profile

    def require_sandbox(self, profile_name: str | None, untrusted: bool) -> SandboxProfile:
        """INV-028: untrusted tools MUST run under a sandbox profile.

        Returns the profile to apply. Raises ``SandboxBypassError`` if an
        untrusted tool tries to run without a sandbox.
        """
        if not untrusted:
            # Trusted tools may run without a sandbox.
            if profile_name and profile_name in self._profiles:
                return self._profiles[profile_name]
            return SandboxProfile(required=False)
        if not profile_name or profile_name not in self._profiles:
            raise SandboxBypassError(
                "INV-028: untrusted tool requires a sandbox profile"
            )
        profile = self._profiles[profile_name]
        if not profile.required:
            # Mark required at enforcement time.
            profile = profile.model_copy(update={"required": True})
        return profile
