# Polymarket US API Authentication

Source: https://docs.polymarket.us (quickstart, API reference, sample code)
Fetched: 2026-06-24

## Retail API Authentication

### Credentials

Generated at polymarket.us/developer after KYC verification.
- Key ID (UUID)
- Secret Key (Ed25519 private key)

### Request Headers

Three headers required on every authenticated request:
- `X-PM-Access-Key`: UUID API key from developer portal
- `X-PM-Timestamp`: Unix milliseconds (must be within 30 seconds of server time)
- `X-PM-Signature`: Base64-encoded Ed25519 signature

### Signature Construction

Sign the string: `timestamp + method + path`

For WebSocket connections: `timestamp + "GET" + path`

### Client Setup (TypeScript)

```typescript
const client = new PolymarketUS({
  keyId: process.env.POLYMARKET_KEY_ID,
  secretKey: process.env.POLYMARKET_SECRET_KEY,
});
```

### Client Setup (Python)

```python
client = PolymarketUS(
    key_id=os.environ["POLYMARKET_KEY_ID"],
    secret_key=os.environ["POLYMARKET_SECRET_KEY"],
)
```

## Exchange API Authentication

Uses Private Key JWT authentication via Auth0.

### Token Acquisition

POST to `https://{auth0-domain}/oauth/token` with a signed JWT client
assertion.

Tokens must be refreshed every 3 minutes across all environments.

### JWT Claims

```python
claims = {
    "iss": client_id,
    "sub": client_id,
    "aud": f"https://{domain}/oauth/token",
    "iat": now,
    "exp": now + 300,
    "jti": str(uuid.uuid4()),
}
```

Signed with RS256 using the private key.

### Python Example

```python
import jwt
import time
import uuid
from cryptography.hazmat.primitives import serialization

def create_client_assertion(client_id, domain, private_key_path):
    with open(private_key_path, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    now = int(time.time())
    claims = {
        "iss": client_id,
        "sub": client_id,
        "aud": f"https://{domain}/oauth/token",
        "iat": now,
        "exp": now + 300,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(claims, private_key, algorithm="RS256")
```

## Error Classes (SDK)

- `AuthenticationError`
- `BadRequestError`
- `NotFoundError`
- `RateLimitError`
- `APITimeoutError`
- `APIConnectionError`
