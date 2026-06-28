# Auth + Connection Layering

How every mountainash package that opens an authenticated connection — `mountainash-data` (DB drivers), `mountainash-transport` (storage SDKs), `mountainash-wearables` (HTTP APIs) — composes **config** and **credentials** into a live client from the same shape, so the next integration copies a pattern instead of inventing one.

Audience: anyone building a connection/backend/auth integration on `mountainash_settings.Profile` + `mountainash-auth-client`, and anyone reconciling why an existing one feels off.

## The rule

Principle: `a.architecture/credentials-are-rendered-by-the-consumer.md`.

> **A profile renders itself to target kwargs only if it is inherently target-specific. Generic credential data does not render itself — the consumer that owns a target renders it.**

Two kinds of profile, and the rule tells them apart by a single test — *is this thing about one target, or about all of them?*

- A **config profile** (`PostgreSQLBackendProfile`, `S3StorageProfile`) is inherently target-specific: a postgres profile is *about* the postgres driver, an S3 profile is *about* boto3. It knows its own driver kwargs → **it renders itself**.
- An **auth profile** (`PasswordAuthProfile`, `TokenAuthProfile`) is target-generic: a username/password is the same fact whether you hand it to postgres, to S3, or to an HTTP API. It does **not** know any target → **it is pure data, and the consumer that has a target renders it**.

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
│      (target-generic)      pure DATA — no methods, no rendering,     │
│                            no target knowledge                       │
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
| L2 auth profile | the raw credential facts | — | (read as data) |
| L3 consumer applier | rendering *this consumer's* creds onto config | auth profile + base dict | finished dict |
| L4 runtime connection | opening the live client | finished dict | client |

## What goes where

**`mountainash-auth-client` holds universal credential data — and only that.** A credential schema carries the facts that are true of the credential regardless of who consumes it: `USERNAME`/`PASSWORD`, a `TOKEN`, `CLIENT_ID`/`CLIENT_SECRET`, AWS keys. It carries **no target rendering and no protocol policy**. If a field or method is only meaningful when talking a specific protocol to a specific kind of endpoint, it does not belong on the generic credential — it belongs in that consumer.

**Each consumer owns its rendering.** L1 (a config profile emitting its own driver kwargs) and L3 (an applier turning generic creds into this target's auth kwargs) both live in the consumer. The consumer is the only place that knows a target, so it is the only place that renders for one.

**The runtime takes a finished dict.** A `Connection` never sees a profile. It is handed the exact kwargs its client constructor wants and does one thing: construct and connect. This keeps connections trivially testable and target-libraries swappable.

## The smells this rule prevents

Each existing package drifted from the rule in one direction; naming the drift is the fastest way to recognise it in new code.

1. **Protocol policy on a generic credential.** An auth schema that carries `SERVER_URI`, `SCOPE`, `TOKEN_EXPIRES_AT`, an authcode-vs-client-credentials split, or a baked-in Bearer-header renderer has stopped being a generic credential and become *an HTTP-OAuth client*. Those shapes belong in the HTTP/OAuth consumer (wearables, or a shared `http-auth` layer), one layer down. Symptom: the generic library looks heavy and the consumer that should own the protocol looks thin.

2. **Double-rendering across tiers.** When L1's flat `driver_key` rename sets `region_name` and a compose hook then *re-reads the profile and overwrites `region_name`*, the two tiers are fighting over the same field. A compose hook **adds** the nested/computed keys flat renames can't express (an `ssl={}` dict, a `Config(...)` object, a folded host); it does not re-derive what `driver_key` already produced. One field, one renderer.

3. **Auth rendering as a factory special-case.** When the factory has to detect an envelope shape (`{"base_kwargs": …}` for assume-role) and route credentials into it, target-specific auth logic has leaked into the generic composer. Envelopes are L3's job: the consumer's applier produces and fills them; the factory only ever does `Connection(apply(auth, config))`.

## How each consumer instantiates the pattern

| | config (L1) | auth applier (L3) | runtime (L4) |
|---|---|---|---|
| **data** | `BackendProfile.emit(provider_type)` — `driver_key` + class-literal `__adapters__` for the 3 non-flat backends | `(provider_type, auth_class) -> fn` table in `ConnectionFactory`, reads `*AuthProfile` fields, imports the DB driver | `IbisBackend`/`IbisConnection`, `IcebergConnection` |
| **transport** | `StorageProfile.emit(family)` | applier reads the `*AuthProfile` and renders boto/paramiko/httpx auth (incl. the assume-role envelope) | `connections/*Connection` |
| **wearables** | provider profile fields | reads creds directly in `connect()` (single-auth providers) / owns its OAuth2 flow types | provider connection objects |

`mountainash-auth-client` is **not** in this table as a consumer. It sits beneath all three, supplying L2 data only.

## Current divergences (to converge)

These are known, tracked deviations — see [known-divergences.md](known-divergences.md):

- **auth-client is over-rich on OAuth2.** `OAuth2AuthProfile` / `OAuth2AuthCodeAuthProfile` carry HTTP-OAuth flow policy (scopes, expiry, server URIs, Bearer rendering). Under the rule these move down to the HTTP/OAuth consumer; auth-client keeps only the universal credential fields.
- **transport double-renders and special-cases envelopes.** The S3 path sets fields via `driver_key` then overwrites them in the compose hook, and the factory special-cases the assume-role envelope. Under the rule the compose hook only adds nested keys, and the envelope is owned by the applier.

New consumers should follow the rule directly rather than copying these divergences. `mountainash-data`'s auth-client migration is the first clean exemplar.

## See also

- `a.architecture/three-layer-separation.md` — the meta-principle this specialises (each layer one responsibility)
- `a.architecture/credentials-are-rendered-by-the-consumer.md` — the rule above
- [backend-architecture.md](backend-architecture.md) — the analogous three-layer split inside the expression/relation engine
- [extension-points.md](extension-points.md) — where downstream packages plug in
