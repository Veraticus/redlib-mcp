# Cloudflare Access OAuth Integration Design

## Overview

Add OAuth 2.0/2.1 authentication to redlib-mcp using Cloudflare Access as the identity provider. This enables MCP clients (like Claude Desktop) to authenticate via browser-based OAuth flow before accessing the server.

## Architecture

The server plays two OAuth roles simultaneously:

```
┌─────────────┐     OAuth      ┌─────────────────┐     OIDC      ┌──────────────────┐
│ MCP Client  │◄──────────────►│  redlib-mcp     │◄─────────────►│ Cloudflare Access│
│ (Claude)    │   (Provider)   │  Python Server  │   (Client)    │  (IdP)           │
└─────────────┘                └─────────────────┘               └──────────────────┘
```

**As OAuth Provider** (to MCP clients):
- Exposes `/.well-known/oauth-authorization-server` metadata
- Handles `/authorize`, `/token`, `/register` endpoints
- Issues JWT access tokens to authenticated clients

**As OIDC Client** (to Cloudflare Access):
- Redirects users to Access for authentication
- Receives callback with authorization code
- Exchanges code for Access tokens, validates identity

## Authentication Flow

```
1. Client GETs /.well-known/oauth-authorization-server
   → Server returns metadata (endpoints, supported grants, etc.)

2. Client POSTs /register (Dynamic Client Registration)
   → Server stores client_id, redirect_uri in memory
   → Returns client credentials

3. Client redirects user to /authorize?client_id=...&redirect_uri=...&state=...
   → Server stores state, redirects to Cloudflare Access

4. User authenticates with Access (via your configured IdP)
   → Access redirects to /callback?code=...&state=...

5. Server exchanges code with Access for tokens
   → Validates ID token, extracts user identity

6. Server generates its own JWT access token
   → Stores session: token → user identity

7. Server redirects to client's redirect_uri with auth code
   → Client exchanges code for server's access token

8. Client includes token in MCP requests
   → Server validates token, allows MCP tool calls
```

Token lifetime: 1 hour (configurable). No refresh tokens—client re-authenticates when expired.

## Configuration

### Cloudflare Side (One-time Setup)

Create an "Access for SaaS" OIDC application in Cloudflare Zero Trust dashboard. This provides:

| Value | Description |
|-------|-------------|
| Client ID | Identifies your MCP server to Access |
| Client Secret | Proves your server's identity |
| Authorization URL | `https://<team>.cloudflareaccess.com/cdn-cgi/access/sso/oidc/<app-id>/authorize` |
| Token URL | `https://<team>.cloudflareaccess.com/cdn-cgi/access/sso/oidc/<app-id>/token` |
| JWKS URL | `https://<team>.cloudflareaccess.com/cdn-cgi/access/certs` |

Configure identity providers and access policies in the dashboard.

### Server Side

Environment variables:

```bash
# Required
export ACCESS_CLIENT_ID="..."
export ACCESS_CLIENT_SECRET="..."
export ACCESS_TEAM_NAME="your-team"

# Optional overrides (derived from team name by default)
export ACCESS_AUTH_URL="..."
export ACCESS_TOKEN_URL="..."
export ACCESS_JWKS_URL="..."
```

## Code Structure

```
src/
├── redlib_mcp.py          # Existing - MCP tools (unchanged)
└── server.py              # New - HTTP server + OAuth
    ├── OAuth Provider     # /authorize, /token, /register, /.well-known/*
    ├── OIDC Client        # Cloudflare Access integration
    ├── Session Store      # In-memory token → identity mapping
    └── Transports         # SSE + Streamable HTTP mounting MCP server
```

### Dependencies

Add to pyproject.toml:
- `starlette` - ASGI framework for HTTP routing
- `uvicorn` - ASGI server
- `pyjwt` - JWT token creation/validation
- `cryptography` - JWT signing (pyjwt dependency)

### Entry Points

- `redlib-mcp` (existing) - stdio transport, no auth
- `redlib-mcp-server` (new) - HTTP server with OAuth

## Endpoints

### Discovery
- `GET /.well-known/oauth-authorization-server` — OAuth metadata
- `GET /.well-known/jwks.json` — Public keys for token verification

### Authorization
- `GET /authorize` — Starts OAuth flow, redirects to Cloudflare Access
- `GET /callback` — Receives Access callback, issues auth code
- `POST /token` — Exchanges auth code for access token

### Dynamic Client Registration
- `POST /register` — Clients register themselves, receive client_id

### MCP Transports (auth-protected)
- `GET /sse` — SSE transport
- `POST /mcp` — Streamable HTTP transport

## Error Handling

### OAuth Errors
- Invalid/expired state → 400 `invalid_request`
- Access denies auth → Redirect with `access_denied`
- Token exchange fails → 500, log server-side
- Invalid client_id → 400 `invalid_client`

### Token Errors
- Missing Authorization header → 401 with `WWW-Authenticate: Bearer`
- Expired token → 401, client re-authenticates
- Invalid signature → 401

### Server Restart
- All sessions invalidated (in-memory storage)
- Signing key regenerated
- Clients must re-authenticate

### Degradation
- Access unreachable → 502 during auth
- JWKS fetch failure → Cache keys, retry with backoff

## Testing

### Unit Tests
- Token generation/validation with mock keys
- OAuth URL construction
- State parameter encoding/decoding
- Session store operations

### Integration Tests
- Full OAuth flow with mocked Cloudflare responses
- Client registration → authorize → callback → token
- Protected endpoint rejection/acceptance

### Manual Testing
- MCP Inspector with real Access
- Claude Desktop connection

## Estimated Scope

| Component | Lines |
|-----------|-------|
| OAuth provider endpoints | ~200 |
| OIDC client (Access) | ~100 |
| Session store | ~50 |
| HTTP server + transports | ~100 |
| Tests | ~300 |
