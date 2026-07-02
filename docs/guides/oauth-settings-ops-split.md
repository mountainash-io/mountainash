# OAuth: Settings / Ops Split

Where OAuth2 lives, and why it stays *in* `mountainash-auth-client` rather than moving out — but as two independent submodules, not one woven tangle.

Audience: maintainers of `mountainash-auth-client`, and any consumer that acquires OAuth tokens (`mountainash-wearables` today; `mountainash-data`'s snowflake/iceberg OAuth backends tomorrow).

Read [auth-connection-layering.md](auth-connection-layering.md) first — this doc is the OAuth-specific application of that guide's rule.

## The decision

**OAuth2 is auth. It stays in `mountainash-auth-client`.** A separate `mountainash-oauth` package was considered and rejected: OAuth needs auth-client's credential schemas to exist at all, so a standalone package buys no real independence — it only fragments the auth domain across two repos. (See the principle `a.architecture/extract-by-responsibility-not-by-consumer.md`: don't over-extract any more than you over-specialise.)

But OAuth must **not be woven through the credential schemas** the way it is today. The fix is internal: split auth-client into two **independent submodules** — generic auth *settings* separate from auth *ops*.

```
mountainash-auth-client  (one package)
│
├── schemas/        AUTH SETTINGS — pure credential DATA
│                     • pydantic only; NO httpx, NO rendering adapters, NO flow logic
│                     • the secrets you persist: USERNAME/PASSWORD, TOKEN,
│                       CLIENT_ID/CLIENT_SECRET, REFRESH_TOKEN
│                     • MUST NOT import oauth/   (one-way dependency)
│
└── oauth/  (ops)   AUTH OPS — OAuth2 flow polymorphism + lifecycle
                      • authcode / client-credentials / device / PKCE
                      • acquire · refresh · callback server · persist · token-state
                      • depends on: schemas (credential data) + httpx (token-endpoint
                        POSTs) + mountainash-secrets (persistence)
                      • does NOT depend on mountainash-http-client
                      • OUTPUT: a fresh token / token-state  ← a generic credential
```

`schemas/ MUST NOT import oauth/` is the load-bearing invariant. It makes the two submodules genuinely independent: a consumer that only reads credential data touches `schemas/` and never pulls in the flow machinery or its httpx-flow code. Enforce it as an **optional extra**:

- `mountainash-auth-client` core = `schemas/` — lightweight, pydantic-only.
- `mountainash-auth-client[oauth]` = the `oauth/` ops submodule — httpx + callback server + secrets.

## What un-weaves (the cost of the current tangle)

Two specific entanglements move:

1. **Rendering comes off the credential schemas.** Today `OAuth2AuthProfile` bakes `__adapters__ = {TargetFamily.HTTP: _bearer_from_token}` *into the data class* — the schema renders an HTTP Bearer header. That is target-rendering on a generic credential (the smell from the layering guide). The schema becomes pure data; Bearer-rendering belongs to whoever applies the token.

2. **Ops outputs a token, not a built client.** Today `connections/oauth2/connection.py:OAuth2Connection.connect()` constructs the consumer's `httpx.Client` with a Bearer baked into its default headers — auth-client reaching into the consumer's transport. Ops should hand back a **token / token-state**; the consumer applies it. This is the layering rule applied recursively: *ops produces a credential, the consumer renders it for its target.*

### Field placement after the split

| Field | Lives in | Why |
|---|---|---|
| `CLIENT_ID`, `CLIENT_SECRET`, `TOKEN`/`ACCESS_TOKEN`, `REFRESH_TOKEN` | `schemas/` (data) | the persisted secrets — credential data |
| `AUTHORIZE_URL`, `TOKEN_URL`, `USE_PKCE`, `SCOPE`, `SERVER_URI`, auth method | provider profile in `oauth/` | provider coordinates — how/where to talk to the IdP |
| `TOKEN_EXPIRES_AT`, token cache state | `oauth/` ops (managed) | live token state, not static data |

The two-variant polymorphism the schemas encode today (`OAuth2AuthProfile` vs `OAuth2AuthCodeAuthProfile`) collapses: the credential *data* is nearly identical; the *flow* difference (client-credentials vs authorization-code) is an `oauth/` ops concern selected by the provider profile, not two near-duplicate data classes.

## How consumers apply the token

The ops submodule produces a token; each consumer renders it for its own target — exactly the layering guide's L3 applier:

| Consumer | Applies the token as | Via |
|---|---|---|
| **wearables** (HTTP APIs) | `Authorization: Bearer …` | a thin `oauth → on_auth_refresh` adapter feeding `mountainash-http-client`'s `HttpConfig.on_auth_refresh` seam — the transport refreshes on 401 natively (today's string-header extraction in `pipelines/shared/fetch.py` disappears) |
| **data** (snowflake / iceberg) | `authenticator=oauth` + `token=` / pyiceberg OAuth2 | its own `(provider_type, auth_class) → fn` auth adapter (the data spec's applier) — **no http-client dependency** |
| future (gRPC, MQ, …) | its own target shape | its own applier |

This is why the package boundary matters: because `oauth/` depends on **httpx + secrets, not http-client**, `mountainash-data` can adopt OAuth token acquisition for snowflake/iceberg (the data spec's §10 deferred lifecycle) without dragging in a REST-fetch pipeline. The token-acquisition is shared; the token-application is per-consumer.

## Dependency graph

```
mountainash-secrets ──┐
                      ├──► auth-client[oauth]  (ops: flow + lifecycle)
httpx ────────────────┤         ▲
                      │         │ imports (one-way)
auth-client/schemas ──┴─────────┘  (data: pure pydantic)
                                  │
        ┌─────────────────────────┼──────────────────────────┐
        ▼                         ▼                            ▼
   wearables                mountainash-data            future consumers
 (token→Bearer via         (token→snowflake/iceberg
  http-client seam)         via its auth applier)

mountainash-http-client stays credential-free; it only exposes the
on_auth_refresh / RequestCreds seam an OAuth adapter plugs into.
```

## Blast radius & status

**Status: design locked, not implemented.** This is a future refactor; nothing depends on it landing first.

- **wearables** consumes `OAuth2Connection` / `OAuth2TokenManager` from auth-client today — it rewires to: ops produces a token, wearables wires the `on_auth_refresh` adapter into `HttpConfig`. Largest blast radius of the three packages.
- **data** does *not* depend on this — it reads static credential data and proceeds on the current auth-client schema surface. It becomes a consumer of `[oauth]` only when/if it implements the §10 acquisition backlog.
- **http-client** is unchanged — it already has the seam.

Sequence: the layering docs lock first, then the data migration builds against the stable schema surface, then this OAuth un-weave and the transport simplification proceed independently. See the convergence backlog in [auth-connection-layering.md](auth-connection-layering.md#convergence-backlog).
