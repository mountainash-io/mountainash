"""Engine translation of transport's native read access.

``mountainash_transport.resolve_native_read`` describes effective access with
transport-owned option names. This module is the only place that turns that
description into Polars/Narwhals ``storage_options`` or into DuckDB temporary
secrets. A configuration an engine cannot express faithfully is *unrepresentable*
(``None``/``False``): the caller then selects the existing transport route
before any data is opened. Nothing here reads data; errors raised after a
setup attempt starts propagate and never select another route.

Representation matrix (``connection_options`` -> engine):

======================  ==========================  ===========================
transport option        Polars ``storage_options``  DuckDB temporary S3 secret
======================  ==========================  ===========================
access_key_id/secret    aws_access_key_id/secret    KEY_ID / SECRET
region                  aws_region                  REGION
endpoint_url (no path)  aws_endpoint_url            ENDPOINT (host[:port])
endpoint scheme/use_ssl aws_allow_http for http     USE_SSL
addressing_style        aws_virtual_hosted_style    URL_STYLE path / vhost
verify_tls              True only (TLS locations)   True, engine must verify
HTTP anonymous          no options                  no secret (no HTTP secret
                                                    may overlap the URL)
======================  ==========================  ===========================

Everything else (connect/read timeouts, accelerate/dualstack, follow_redirects,
max_redirects, headers, ``verify_tls=False`` on TLS, unknown options, missing or
ambient credentials, non-``s3``/``http(s)`` providers, S3 Express buckets, glob
characters in a remote location) is unrepresentable. ``auto`` addressing resolves
as botocore does: path style behind a custom endpoint, otherwise virtual-hosted
for DNS-compatible buckets.

DuckDB state is shared by every connection to one database instance, so
compatibility is decided from the engine's own catalog (``duckdb_secrets()``,
``duckdb_settings()``, ``duckdb_extensions()``), never from a wrapper. The only
adapter-owned association is the secret *name*: a keyed digest of the secret's
complete configuration. A secret carrying that name, with the expected type and
scope, is by construction this adapter's compatible setup; any other secret whose
scope overlaps the new scope (in either prefix direction) is a conflict.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence
    from mountainash_transport import NativeReadAccess

__all__ = [
    "duckdb_native_eligible",
    "duckdb_setup_required",
    "polars_storage_options",
    "setup_duckdb",
]

_S3_OPTIONS = frozenset({
    "access_key_id", "secret_access_key", "region", "endpoint_url",
    "use_ssl", "verify_tls", "addressing_style",
})
_HTTP_OPTIONS = frozenset({"anonymous", "verify_tls"})
_GLOB_CHARACTERS = "*?["
_DNS_BUCKET = re.compile(r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$")
_SECRET_PREFIX = "mashn_s3_"
# Keyed so a visible secret name cannot be used to confirm guessed credentials.
_NAME_KEY = secrets.token_bytes(32)
_SETUP_LOCK = threading.Lock()
_ENGINE_SETTINGS = (
    "enable_external_access", "disabled_filesystems", "autoinstall_known_extensions",
    "httpfs_client_implementation", "enable_curl_server_cert_verification",
    "enable_server_cert_verification",
)


# --------------------------------------------------------------------------
# Access normalization shared by both engines
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class _S3:
    bucket: str
    key_id: str = field(repr=False)
    secret: str = field(repr=False)
    region: str
    endpoint_url: str | None  # as configured, normalized without a trailing slash
    host: str | None  # host[:port] of the endpoint
    tls: bool
    virtual: bool

    @property
    def scope(self) -> str:
        return f"s3://{self.bucket}/"

    @property
    def name(self) -> str:
        identity = json.dumps(
            [self.key_id, self.secret, self.region, self.host, self.tls, self.virtual, self.scope]
        )
        return _SECRET_PREFIX + hmac.new(_NAME_KEY, identity.encode(), hashlib.sha256).hexdigest()[:32]


@dataclass(frozen=True)
class _Http:
    location: str
    tls: bool


def _has_glob(location: str) -> bool:
    return any(c in location for c in _GLOB_CHARACTERS)


def _s3(access: NativeReadAccess) -> _S3 | None:
    options = access.connection_options
    if access.scheme != "s3" or not set(options) <= _S3_OPTIONS or _has_glob(access.location):
        return None
    key_id, secret = options.get("access_key_id"), options.get("secret_access_key")
    if not key_id or not secret:
        return None  # ambient/absent credentials are never exported or defaulted
    try:
        location = urlsplit(access.location)
    except ValueError:
        return None
    bucket = location.netloc
    if location.scheme != "s3" or not bucket or "@" in bucket or ":" in bucket:
        return None
    if bucket.endswith("--x-s3"):
        return None  # S3 Express resolves zonal endpoints inside the SDK

    endpoint_url = options.get("endpoint_url")
    host: str | None = None
    if endpoint_url:
        try:
            endpoint = urlsplit(str(endpoint_url))
        except ValueError:
            return None
        if (
            endpoint.scheme not in ("http", "https") or not endpoint.netloc or "@" in endpoint.netloc
            or endpoint.path not in ("", "/") or endpoint.query or endpoint.fragment
        ):
            return None
        host, tls = endpoint.netloc, endpoint.scheme == "https"
        endpoint_url = f"{endpoint.scheme}://{endpoint.netloc}"
    else:
        endpoint_url, tls = None, bool(options.get("use_ssl", True))
        if not tls:
            return None  # plain-HTTP AWS has no faithful engine spelling

    if tls and not bool(options.get("verify_tls", True)):
        return None

    style = options.get("addressing_style", "auto")
    dns_compatible = _DNS_BUCKET.match(bucket) is not None
    if host:
        if style == "virtual" and not dns_compatible:
            return None  # botocore's fallback differs by endpoint scheme
        virtual = style == "virtual"
    else:
        virtual = style != "path" and dns_compatible
    return _S3(
        bucket, str(key_id), str(secret), str(options.get("region") or "us-east-1"),
        endpoint_url, host, tls, virtual,
    )


def _http(access: NativeReadAccess) -> _Http | None:
    options = access.connection_options
    if (
        access.scheme not in ("http", "https") or not set(options) <= _HTTP_OPTIONS
        or options.get("anonymous") is not True or _has_glob(access.location)
    ):
        return None
    tls = access.scheme == "https"
    if tls and not bool(options.get("verify_tls", True)):
        return None
    return _Http(access.location, tls)


# --------------------------------------------------------------------------
# Polars / Narwhals-Polars
# --------------------------------------------------------------------------


def polars_storage_options(access: NativeReadAccess) -> dict[str, str] | None:
    """Immutable-by-construction ``storage_options`` for *access*.

    ``{}`` for local files and anonymous HTTP(S); ``None`` when Polars cannot
    represent the access faithfully. S3 options carry an explicit empty
    ``aws_session_token`` so an ambient token cannot join the static credentials.
    """
    if access.scheme == "file":
        return {}
    if access.scheme in ("http", "https"):
        return {} if _http(access) is not None else None
    s3 = _s3(access)
    if s3 is None:
        return None
    options = {
        "aws_access_key_id": s3.key_id,
        "aws_secret_access_key": s3.secret,
        "aws_region": s3.region,
        "aws_virtual_hosted_style_request": "true" if s3.virtual else "false",
        "aws_session_token": "",  # an explicit empty token overrides ambient AWS_SESSION_TOKEN
    }
    if s3.endpoint_url:
        options["aws_endpoint_url"] = s3.endpoint_url
        if not s3.tls:
            options["aws_allow_http"] = "true"
    return options


# --------------------------------------------------------------------------
# DuckDB
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class _Engine:
    """Read-only snapshot of the actual database instance's relevant state."""

    httpfs_loaded: bool
    httpfs_installed: bool
    settings: Mapping[str, str | None]
    secrets: tuple[tuple[str, str, bool, str, tuple[str, ...]], ...]  # name, type, persistent, storage, scopes
    version: tuple[int, ...]


@dataclass(frozen=True)
class _Plan:
    missing: tuple[_S3, ...]
    needs_extension: bool  # remote access and httpfs not yet loaded on this database
    httpfs_installed: bool


def _verifies_tls(engine: _Engine) -> bool:
    """Whether the HTTP client httpfs will actually use verifies server certificates.

    Observed on DuckDB 1.5.6 against a self-signed server: the ``default`` and
    ``curl`` clients obey only ``enable_curl_server_cert_verification``;
    ``httplib`` obeys only ``enable_server_cert_verification``. Before httpfs is
    loaded its settings do not exist; its 1.5 default is the verifying curl client.
    """
    if not engine.httpfs_loaded:
        return engine.version >= (1, 5)
    settings = engine.settings
    client = settings.get("httpfs_client_implementation") or "default"
    curl = settings.get("enable_curl_server_cert_verification")
    if client in ("default", "curl") and curl is not None:
        return curl.lower() == "true"
    if client in ("default", "httplib"):
        return (settings.get("enable_server_cert_verification") or "").lower() == "true"
    return False


@contextmanager
def _cursor(native: Any) -> Iterator[Any]:
    # Setup statements affect the whole database; a cursor leaves the caller's
    # result sets on the main connection untouched.
    cursor = native.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


def _snapshot(native: Any) -> _Engine:
    # Ibis executes reads on this connection, whose session ``SET`` values a fresh
    # cursor would not see; extensions and secrets are database-wide either way.
    names = ", ".join(f"'{n}'" for n in _ENGINE_SETTINGS)
    extension = native.execute(
        "SELECT loaded, installed FROM duckdb_extensions() WHERE extension_name = 'httpfs'"
    ).fetchone() or (False, False)
    settings = dict(native.execute(
        f"SELECT name, value FROM duckdb_settings() WHERE name IN ({names})"
    ).fetchall())
    rows = native.execute("SELECT name, type, persistent, storage, scope FROM duckdb_secrets()").fetchall()
    version = native.execute("SELECT library_version FROM pragma_version()").fetchone()[0]
    return _Engine(
        bool(extension[0]), bool(extension[1]), settings,
        tuple((n, t, bool(p), s, tuple(sc or ())) for n, t, p, s, sc in rows),
        tuple(int(part) for part in version.lstrip("v").split(".")[:2]),
    )


def _overlaps(a: str, b: str) -> bool:
    return a.startswith(b) or b.startswith(a)


def _plan(accesses: Sequence[NativeReadAccess], connection: Any) -> _Plan | None:
    """Decide from actual engine state; ``None`` selects the transport route."""
    remote = [a for a in accesses if a.scheme != "file"]
    if not remote:
        return _Plan((), False, True)

    targets: list[_S3 | _Http] = []
    for access in remote:
        target = _s3(access) if access.scheme == "s3" else _http(access)
        if target is None:
            return None
        targets.append(target)
    engine = _snapshot(connection.con)

    settings = engine.settings
    if (settings.get("enable_external_access") or "true").lower() == "false":
        return None
    disabled = settings.get("disabled_filesystems") or ""
    if "HTTPFileSystem" in disabled or "S3FileSystem" in disabled:
        return None
    if not (
        engine.httpfs_loaded or engine.httpfs_installed
        or (settings.get("autoinstall_known_extensions") or "true").lower() == "true"
    ):
        return None  # genuinely unavailable under the caller's configuration
    if any(t.tls for t in targets) and not _verifies_tls(engine):
        return None  # the client httpfs would use does not verify certificates

    seen: dict[str, str] = {}  # scope -> secret name
    missing: dict[str, _S3] = {}  # secret name -> target
    for target in targets:
        if isinstance(target, _Http):
            if any(
                kind == "http" and any(target.location.startswith(s) for s in scopes or ("",))
                for _, kind, _, _, scopes in engine.secrets
            ):
                return None  # a caller secret would add credentials/headers: not anonymous
            continue
        if seen.setdefault(target.scope, target.name) != target.name:
            return None  # same scope, different configuration within one request
        ready = False
        for name, kind, persistent, storage, scopes in engine.secrets:
            if kind != "s3":
                continue
            if name == target.name:
                if persistent or storage != "memory" or scopes != (target.scope,):
                    return None
                ready = True
            elif any(_overlaps(target.scope, scope) for scope in scopes or ("",)):
                return None
        if not ready:
            missing[target.name] = target
    return _Plan(tuple(missing.values()), not engine.httpfs_loaded, engine.httpfs_installed)


def duckdb_native_eligible(accesses: Sequence[NativeReadAccess], connection: Any) -> bool:
    """True when DuckDB can read *accesses* natively on *connection*'s database.

    Only queries engine metadata; never loads, installs, creates or reads. Local
    accesses need nothing, so a list without remote accesses is eligible.
    """
    return _plan(accesses, connection) is not None


def duckdb_setup_required(accesses: Sequence[NativeReadAccess], connection: Any) -> bool:
    """True when :func:`setup_duckdb` must still load httpfs or create secrets.

    False for an ineligible (fallback) request and when the extension is loaded
    and every needed secret is already present. Never mutates.
    """
    plan = _plan(accesses, connection)
    return plan is not None and bool(plan.missing or plan.needs_extension)


def setup_duckdb(accesses: Sequence[NativeReadAccess], connection: Any) -> bool:
    """Create the temporary secrets *accesses* need on *connection*'s database.

    Returns ``False`` only when a conflict is found before anything changes (the
    caller then falls back). Successful setup stays for the database's lifetime.
    A failure rolls back only the secrets this attempt created and re-raises,
    with credential values removed from the displayed message.
    """
    with _SETUP_LOCK:
        plan = _plan(accesses, connection)
        if plan is None:
            return False
        if not plan.missing and not plan.needs_extension:
            return True
        native = connection.con
        created: list[str] = []
        try:
            with _cursor(native) as cursor:
                if plan.needs_extension:
                    if not plan.httpfs_installed:
                        cursor.execute("INSTALL httpfs")
                    cursor.execute("LOAD httpfs")
                for target in plan.missing:
                    # Explicit empty token/endpoint keep ambient AWS_SESSION_TOKEN and caller
                    # s3_session_token/s3_endpoint settings (httpfs seeds them from the
                    # environment) out of this secret without changing that global state.
                    fields = {
                        "KEY_ID": target.key_id, "SECRET": target.secret, "SESSION_TOKEN": "",
                        "REGION": target.region,
                        "URL_STYLE": "vhost" if target.virtual else "path", "USE_SSL": target.tls,
                        "ENDPOINT": target.host or "", "SCOPE": target.scope,
                    }
                    assignments = ", ".join(f"{key} ?" for key in fields)
                    cursor.execute(
                        f'CREATE TEMPORARY SECRET "{target.name}" (TYPE s3, {assignments})',
                        list(fields.values()),
                    )
                    created.append(target.name)
        except Exception as exc:
            if created:
                with _cursor(native) as cursor:
                    for name in created:
                        cursor.execute(f'DROP TEMPORARY SECRET IF EXISTS "{name}"')
            safe = _redacted(exc, [v for t in plan.missing for v in (t.key_id, t.secret)])
            if safe is exc:
                raise
            raise safe from None
        return True


def _redacted(exc: Exception, values: Sequence[str]) -> Exception:
    text = str(exc)
    clean = text
    for value in values:
        clean = clean.replace(value, "***")
    if clean == text:
        return exc
    try:
        return type(exc)(clean)
    except Exception:
        return RuntimeError(clean)
