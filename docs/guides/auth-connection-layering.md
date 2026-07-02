# Auth + Connection Layering

How every mountainash package that opens an authenticated connection — `mountainash-data` (DB drivers), `mountainash-transport` (storage SDKs), `mountainash-wearables` (HTTP APIs) — composes **config** and **credentials** into a live client from the same shape, so the next integration copies a pattern instead of inventing one.

Audience: anyone building a connection/backend/auth integration on `mountainash_settings.Profile` + `mountainash-auth-client`, and anyone reconciling why an existing one feels off.

## The rule

Principle: `a.architecture/credentials-are-rendered-by-the-consumer.md`.

> **A config profile renders itself to target kwargs — it is inherently target-specific. A generic credential is data plus reusable renderers for the target families the package itself owns, reached through `emit(target)`; the consumer applies it — invoking that renderer for a package-owned target, or writing its own adapter when it needs a different target or shape.**

Two kinds of profile, and the rule tells them apart by a single test — *is this thing about one target, or about all of them?*

- A **config profile** (`PostgreSQLBackendProfile`, `S3StorageProfile`) is inherently target-specific: a postgres profile is *about* the postgres driver, an S3 profile is *about* boto3. It knows its own driver kwargs → **it renders itself**.
- An **auth profile** (`PasswordAuthProfile`, `TokenAuthProfile`) is target-generic: a username/password is the same fact whether you hand it to postgres, to S3, or to an HTTP API. It carries **no protocol policy**, but it **ships reusable renderers for the target families the package itself owns** (HTTP/BOTO/PARAMIKO), reached via `emit(target)` — sanctioned 1:M reuse. The consumer chooses the target and applies it, invoking that renderer or writing its **own adapter** for a different target or shape.

That asymmetry is the whole pattern. It is not an inconsistency — it is the consistent rule applied to two different kinds of thing.

## The four layers

```
┌─────────────────────────────────────────────────────────────────────┐
│  L1  Config profile        profile.emit(target) -> dict             │
│      (target-specific)     renders ITSELF: driver_key renames for   │
│                            flat fields + one compose hook for nested │
└───────────────────────┬─────────────────────────────────────────────┘
                        │  config kwargs (a dict)
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  L2  Auth profile          PasswordAuthProfile(USERNAME, PASSWORD)  │
│      (target-generic)      DATA + reusable renderers for its own     │
│                            families via emit(); no protocol policy   │
└───────────────────────┬─────────────────────────────────────────────┘
                        │  read by ↓
┌─────────────────────────────────────────────────────────────────────┐
│  L3  Consumer applier      apply(auth_profile, base) -> dict        │
│      (target-specific,     the ONLY place generic creds meet a       │
│       consumer-owned)      target; owns envelopes (assume-role, …)   │
│                                                                      │
│      Factory: Connection(apply(auth, profile.emit(target)))         │
│               order is fixed — config, then auth, then runtime       │
└───────────────────────┬─────────────────────────────────────────────┘
                        │  finished kwargs (a dict)
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  L4  Runtime Connection    Connection(kwargs).connect() -> client   │
│                            takes a finished dict, nothing else       │
└─────────────────────────────────────────────────────────────────────┘
```

Each layer has one responsibility and one interface. Read top to bottom, **dicts flow strictly downward**: the only non-dict inputs are the two source profiles, each at its own render step. There is no step where you have to ask "is this a profile or a dict, and in what order?" — the answer is fixed by the layer.

| Layer | Owns | Input | Output |
|---|---|---|---|
| L1 config profile | this backend's driver config | (itself) | config dict |
| L2 auth profile | credential facts + own-family renderers | — | data, or `emit(target)` |
| L3 consumer applier | rendering *this consumer's* creds onto config | auth profile + base dict | finished dict |
| L4 runtime connection | opening the live client | finished dict | client |

## What goes where

**`mountainash-auth-client` holds universal credential data plus its own-family renderers.** A credential schema carries the facts that are true of the credential regardless of who consumes it: `USERNAME`/`PASSWORD`, a `TOKEN`, `CLIENT_ID`/`CLIENT_SECRET`, AWS keys — plus **reusable renderers for the target families the package itself owns** (HTTP/BOTO/PARAMIKO), reached via `emit(target)`. It carries **no protocol policy**: if a field encodes a *protocol choice* — a server URI, a token-expiry clock, an authcode-vs-client-credentials split — it does not belong on the generic credential; it belongs in the consumer that owns that protocol. Rendering is a capability the package provides; protocol policy is the consumer's choice.

**Each consumer owns how it applies a credential.** L1 (a config profile emitting its own driver kwargs) and L3 (an applier turning generic creds into this target's auth kwargs) both live in the consumer. The consumer owns the *choice* of target and any bespoke reshaping — but for a target family the credential already renders (HTTP/BOTO/PARAMIKO) it applies by invoking `emit(target)` rather than re-hand-rolling; it writes its own adapter only when it needs a shape the shipped renderer does not produce.

**The runtime takes a finished dict.** A `Connection` never sees a profile. It is handed the exact kwargs its client constructor wants and does one thing: construct and connect. This keeps connections trivially testable and target-libraries swappable.

## The smells this rule prevents

Each existing package drifted from the rule in one direction; naming the drift is the fastest way to recognise it in new code.

1. **Protocol policy on a generic credential.** An auth schema that carries `SERVER_URI`, `TOKEN_EXPIRES_AT`, or an authcode-vs-client-credentials split has stopped being a generic credential and become *an HTTP-OAuth client*. Those *policy* shapes belong in the HTTP/OAuth consumer (wearables, or a shared `http-auth` layer), one layer down. Mind the boundary: the credential's own `emit(target)` renderers for the families the package owns (a Bearer-header builder, the BOTO/PARAMIKO shapers) are **not** this smell — they are sanctioned 1:M reuse; and per-user *grant data* such as `SCOPE` stays on the credential. The smell is protocol *policy*, not *rendering*. Symptom: the generic library looks heavy and the consumer that should own the protocol looks thin.

2. **Double-rendering across tiers.** When L1's flat `driver_key` rename sets `region_name` and a compose hook then *re-reads the profile and overwrites `region_name`*, the two tiers are fighting over the same field. A compose hook **adds** the nested/computed keys flat renames can't express (an `ssl={}` dict, a `Config(...)` object, a folded host); it does not re-derive what `driver_key` already produced. One field, one renderer.

3. **Auth rendering as a factory special-case.** When the factory has to detect an envelope shape (`{"base_kwargs": …}` for assume-role) and route credentials into it, target-specific auth logic has leaked into the generic composer. Envelopes are L3's job: the consumer's applier produces and fills them; the factory only ever does `Connection(apply(auth, config))`.

## How each consumer instantiates the pattern

| | config (L1) | auth applier (L3) | runtime (L4) |
|---|---|---|---|
| **data** | `BackendProfile.emit(provider_type)` — `driver_key` + class-literal `__adapters__` for the 3 non-flat backends | `(provider_type, auth_class) -> fn` table in `ConnectionFactory`, reads `*AuthProfile` fields, imports the DB driver | `IbisBackend`/`IbisConnection`, `IcebergConnection` |
| **transport** | `StorageProfile.emit(family)` | applier reads the `*AuthProfile` and renders boto/paramiko/httpx auth (incl. the assume-role envelope) | `connections/*Connection` |
| **wearables** | provider profile fields | reads creds directly in `connect()` (single-auth providers) / owns its OAuth2 flow types | provider connection objects |

`mountainash-auth-client` is **not** in this table as a consumer. It sits beneath all three, supplying L2 data only.

## OAuth is the rule applied twice

OAuth2 looks like an exception — it has a whole flow engine (authorize, exchange, refresh, callback). It isn't. Token **acquisition** is an auth operation that *produces a credential*; token **application** renders that credential onto a target. So the rule applies recursively: the OAuth ops layer produces a token (generic credential data), and each consumer renders that token for its target — Bearer header for an HTTP API, `authenticator=oauth` for snowflake. Nothing about OAuth contradicts the layering; it is L2-produced-by-ops feeding L3-per-consumer. The full design is in [oauth-settings-ops-split.md](oauth-settings-ops-split.md).

## Sizing the extraction

Principle: `a.architecture/extract-by-responsibility-not-by-consumer.md`.

The recurring failure mode in this ecosystem is mis-sizing where a concern lives — in *both* directions:

- **Over-specialising** — fitting shared infrastructure to the consumers we *have* rather than the consumers we *could* have. Symptom: the "simple" option forces an *unrelated* consumer to take on dependencies it has no use for (e.g. making OAuth a subpackage of http-client would force `mountainash-data` to depend on a REST-fetch pipeline just to get a database token). That is coupling wearing a simplification's clothes.
- **Over-extracting** — splitting a concern into its own package for independence it can't actually have. Symptom: the extracted package still depends on the thing it split from for its reason to exist (e.g. a standalone `mountainash-oauth` still needs auth-client's credential schemas — so it fragments the auth domain for no real independence).

The test for the right size: **extract by responsibility, and let dependencies flow one way.** A concern earns a *submodule* when it's a distinct responsibility (OAuth ops vs auth settings); it earns a *package* only when it has consumers that don't need its neighbours. When unsure, prefer the smaller boundary (submodule) that keeps the domain cohesive and the dependency one-directional.

## Convergence backlog

Two existing packages predated this rule. **auth-client's drift is now resolved** (the OAuth settings/ops split — Phase 1-3, 2026-06/07); **transport's remains**. They were **architecture debt** (not in the auto-generated cross-backend `known-divergences.md`, which is a different catalog). New work follows the rule directly; `mountainash-data`'s auth-client migration is the first clean exemplar.

- **auth-client wove OAuth ops through the credential schemas** — *resolved (Phase 3).* `OAuth2AuthProfile` previously carried OAuth *policy* (`SERVER_URI`, `TOKEN_EXPIRES_AT`, an authcode split) and `OAuth2Connection` built the consumer's `httpx.Client`. Now: independent `schemas/` (data + own-family renderers) and `oauth/` (ops) submodules; the lifecycle seam (`acquire()`/`force_refresh()`/`acquire_auth()`) outputs a token/credential, **not** a client; `OAuth2Connection`/`OAuth1Connection` are retired; the consumer + `mountainash-http-client` build the client. The HTTP Bearer renderer **stays** on the credential (`__adapters__`, via `emit`) as sanctioned reuse — that was never the smell; the OAuth *policy* was. Full design: [oauth-settings-ops-split.md](oauth-settings-ops-split.md). **Not** "evict OAuth from auth-client" — OAuth is auth.
- **transport double-renders and special-cases envelopes.** The S3 path sets fields via `driver_key` then *overwrites* them in the compose hook, and the factory special-cases the assume-role `base_kwargs` envelope. Target: the compose hook only *adds* nested keys it can't express flatly; the envelope is owned by the L3 applier, never the factory.

## See also

- `a.architecture/three-layer-separation.md` — the meta-principle this specialises (each layer one responsibility)
- `a.architecture/credentials-are-rendered-by-the-consumer.md` — the rule above
- `a.architecture/extract-by-responsibility-not-by-consumer.md` — sizing the boundary
- [oauth-settings-ops-split.md](oauth-settings-ops-split.md) — OAuth as the recursive application
- [backend-architecture.md](backend-architecture.md) — the analogous three-layer split inside the expression/relation engine
- [extension-points.md](extension-points.md) — where downstream packages plug in
