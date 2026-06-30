# httpx

Modern async HTTP client for Python 3.9+. Replacement for `requests` with async support, HTTP/2, connection pooling, and type annotations. Built on [HTTPCore](https://github.com/encode/httpcore).

## Installation

```
uv add httpx
uv add 'httpx[http2]'     # HTTP/2 support
uv add 'httpx[cli]'       # command-line client
uv add 'httpx[brotli,zstd]'  # compression
```

Core dependencies: httpcore, h11, certifi, idna, sniffio.
(source: httpx-api-reference.md)

## Why httpx over requests

- Async support via `AsyncClient` — concurrent API calls without threads
- Connection pooling built in — reuses TCP connections across requests
- HTTP/2 support (opt-in)
- Streaming responses for large payloads
- Type-annotated API
- Timeouts enabled by default (5 seconds; requests has none)
- `content=` vs `data=` separation for request bodies
(source: httpx-quickstart.md, httpx-compatibility.md)

## Core Pattern: Client

Always use a client instance, never bare `httpx.get()`. The top-level functions don't support connection pooling or HTTP/2.

```python
# Sync
with httpx.Client(base_url="https://api.example.com") as client:
    r = client.get("/endpoint", params={"key": "value"})
    data = r.json()

# Async (preferred for concurrent API calls)
async with httpx.AsyncClient(base_url="https://api.example.com") as client:
    r = await client.get("/endpoint", params={"key": "value"})
    data = r.json()
```

The `base_url` parameter eliminates repeated URL construction. One client per API.
(source: httpx-advanced-clients.md, httpx-api-reference.md)

## Client Configuration

```python
timeout = httpx.Timeout(connect=2.0, read=10.0, write=10.0, pool=2.0)
limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)

async with httpx.AsyncClient(
    base_url="https://trading-api.kalshi.com",
    timeout=timeout,
    limits=limits,
    headers={"Accept": "application/json"},
    follow_redirects=True,
) as client:
    ...
```

Client-level headers, params, and cookies **merge** with per-request values. Other parameters (timeout, auth) are **overridden** by per-request values.
(source: httpx-advanced-clients.md)

## Request Methods

All methods available on `Client` and `AsyncClient`:

```python
client.get(url, params=..., headers=..., cookies=..., auth=..., timeout=..., follow_redirects=...)
client.post(url, content=..., data=..., files=..., json=...)
client.put(url, ...)
client.patch(url, ...)
client.delete(url)
client.head(url)
client.options(url)
client.request(method, url, ...)   # generic — allows body on GET/DELETE/etc.
client.stream(method, url, ...)    # streaming context manager
client.build_request(method, url, ...)  # build without sending
client.send(request)               # send a pre-built Request
```

GET, DELETE, HEAD, OPTIONS do not accept `content`, `data`, `files`, or `json`. Use `client.request(method=..., ...)` if you need a body on those methods.
(source: httpx-api-reference.md, httpx-compatibility.md)

## Request Bodies

```python
# JSON (sets Content-Type: application/json)
client.post("/endpoint", json={"key": "value"})

# Form data (Content-Type: application/x-www-form-urlencoded)
client.post("/endpoint", data={"key": "value"})

# Raw bytes/text
client.post("/endpoint", content=b"raw bytes")

# Multipart file upload (Content-Type: multipart/form-data)
with open("file.csv", "rb") as f:
    client.post("/upload", files={"file": f})

# File with explicit name and content type
files = {"file": ("report.csv", file_bytes, "text/csv")}
client.post("/upload", files=files, data={"description": "Q1 report"})
```

`data=<bytes>` is deprecated — use `content=` for raw content, `data=` for form fields.
(source: httpx-quickstart.md, httpx-compatibility.md)

## URL Parameters

```python
params = {"key1": "value1", "key2": "value2"}
r = client.get("/search", params=params)
# URL: /search?key1=value1&key2=value2

# Multiple values for one key
params = {"key": ["a", "b", "c"]}
r = client.get("/search", params=params)
# URL: /search?key=a&key=b&key=c
```

Unlike `requests`, HTTPX does **not** omit params with `None` values. List-of-tuples syntax is not supported — use dict with list values.
(source: httpx-quickstart.md, httpx-compatibility.md)

## Response Object

```python
r = await client.get("/markets")

r.status_code          # int — 200, 404, etc.
r.reason_phrase        # str — "OK", "Not Found"
r.http_version         # "HTTP/1.1" or "HTTP/2"
r.url                  # URL object (use str(r.url) for string)
r.headers              # Headers — case-insensitive dict
r.cookies              # Cookies — dict-like
r.content              # bytes — raw response body
r.text                 # str — decoded response body
r.encoding             # str or None — detected encoding
r.json()               # parsed JSON
r.elapsed              # timedelta — request duration
r.is_success           # bool — True for 2xx (replaces requests' is_ok)
r.is_redirect          # bool
r.request              # the originating Request
r.next_request         # next redirect request (if any)
r.history              # list of redirect responses
r.raise_for_status()   # raises HTTPStatusError on 4xx/5xx, returns self on 2xx
```

`raise_for_status()` returns the response, enabling chaining:
```python
data = (await client.get("/endpoint")).raise_for_status().json()
```
(source: httpx-quickstart.md, httpx-api-reference.md)

## Headers

Response headers are a case-insensitive `Headers` dict. Multiple values for the same header are comma-joined per RFC 7230.

```python
r.headers["Content-Type"]     # case-insensitive
r.headers.get("x-custom")     # returns None if missing
```

Custom request headers:
```python
r = client.get("/endpoint", headers={"Authorization": "Bearer token"})
```
(source: httpx-quickstart.md)

## Cookies

```python
# Read from response
r.cookies["session_id"]

# Send cookies
r = client.get("/endpoint", cookies={"session": "abc123"})

# Domain-scoped cookies
cookies = httpx.Cookies()
cookies.set("token", "xyz", domain="api.kalshi.com")

# When using a Client, set cookies on the client, not per-request
client = httpx.Client(cookies=cookies)
```

Per-request cookies on a Client instance are **not supported** — always set on the client.
(source: httpx-quickstart.md, httpx-compatibility.md)

## Timeouts

HTTPX enforces a 5-second default timeout. Four granular timeout types:

| Type | Triggers | Exception |
|---|---|---|
| connect | socket connection establishment | `ConnectTimeout` |
| read | waiting for response data chunks | `ReadTimeout` |
| write | sending request data chunks | `WriteTimeout` |
| pool | acquiring a connection from the pool | `PoolTimeout` |

```python
# Simple: same timeout for everything
client = httpx.Client(timeout=10.0)

# Disable timeouts entirely
client = httpx.Client(timeout=None)

# Fine-grained: long connect, shorter read/write
timeout = httpx.Timeout(10.0, connect=60.0)
client = httpx.Client(timeout=timeout)

# Per-request override
r = client.get("/slow-endpoint", timeout=30.0)
```
(source: httpx-advanced-timeouts.md)

## Connection Pool Limits

```python
limits = httpx.Limits(
    max_connections=100,           # total connections (default 100)
    max_keepalive_connections=20,  # idle keep-alive connections (default 20)
    keepalive_expiry=5,            # seconds before idle connections expire (default 5)
)
client = httpx.Client(limits=limits)
```
(source: httpx-advanced-resource-limits.md)

## Streaming Responses

For large downloads without loading the entire body into memory:

```python
# Sync
with client.stream("GET", "/large-dataset") as r:
    for chunk in r.iter_bytes():
        process(chunk)

# Async
async with client.stream("GET", "/large-dataset") as r:
    async for chunk in r.aiter_bytes():
        process(chunk)
```

Streaming methods:
- `iter_bytes()` / `aiter_bytes()` — decoded binary chunks
- `iter_text()` / `aiter_text()` — decoded text chunks
- `iter_lines()` / `aiter_lines()` — text line by line (normalized to `\n`)
- `iter_raw()` / `aiter_raw()` — raw bytes without HTTP content decoding
- `read()` / `aread()` — read entire body, making `.text` and `.content` available

Inside a stream block, `.content` and `.text` raise errors unless you call `.read()` first.
(source: httpx-quickstart.md, httpx-async-support.md)

## Redirects

HTTPX does **not** follow redirects by default (unlike `requests`).

```python
# Per-request
r = client.get("/old-path", follow_redirects=True)

# Client-level default
client = httpx.Client(follow_redirects=True)

# Manual redirect following
r = client.get("/endpoint")
if r.is_redirect:
    next_r = client.send(r.next_request)

r.history  # list of followed redirect responses
```
(source: httpx-quickstart.md, httpx-compatibility.md)

## Authentication

```python
# Basic auth (per-request or client-level)
client.get("/endpoint", auth=("username", "password"))
client = httpx.Client(auth=("username", "password"))

# Digest auth
auth = httpx.DigestAuth("username", "password")
client.get("/endpoint", auth=auth)

# Custom auth — subclass httpx.Auth
class KalshiAuth(httpx.Auth):
    requires_request_body = False

    def auth_flow(self, request):
        # modify request (add headers, sign, etc.)
        request.headers["Authorization"] = compute_signature(request)
        yield request
```

Custom auth flows can yield multiple requests and inspect responses (for challenge-response schemes). For async-specific auth, override `.sync_auth_flow()` and `.async_auth_flow()` separately.
(source: httpx-quickstart.md, httpx-advanced-authentication.md)

## Exception Hierarchy

```
HTTPError
├── RequestError                    # network/transport failures (.request attr)
│   ├── TransportError
│   │   ├── TimeoutException
│   │   │   ├── ConnectTimeout
│   │   │   ├── ReadTimeout
│   │   │   ├── WriteTimeout
│   │   │   └── PoolTimeout
│   │   ├── NetworkError
│   │   │   ├── ConnectError
│   │   │   ├── ReadError
│   │   │   ├── WriteError
│   │   │   └── CloseError
│   │   ├── ProtocolError
│   │   │   ├── LocalProtocolError
│   │   │   └── RemoteProtocolError
│   │   ├── ProxyError
│   │   └── UnsupportedProtocol
│   ├── DecodingError
│   └── TooManyRedirects
└── HTTPStatusError                 # 4xx/5xx (.request + .response attrs)

InvalidURL                          # standalone
CookieConflict                      # standalone
StreamError                         # standalone
├── StreamConsumed
├── ResponseNotRead
├── RequestNotRead
└── StreamClosed
```

Standard error handling:
```python
try:
    r = await client.get("/endpoint")
    r.raise_for_status()
except httpx.HTTPStatusError as exc:
    # 4xx/5xx — has exc.response and exc.request
    print(f"{exc.response.status_code} for {exc.request.url}")
except httpx.RequestError as exc:
    # network error — has exc.request only
    print(f"Request failed: {exc.request.url}")
```

Catch-all:
```python
except httpx.HTTPError as exc:
    # catches both RequestError and HTTPStatusError
```
(source: httpx-exceptions.md, httpx-quickstart.md)

## HTTP/2

Not enabled by default. Requires optional dependency:

```
uv add 'httpx[http2]'
```

```python
client = httpx.AsyncClient(http2=True)
r = await client.get("https://example.com")
print(r.http_version)  # "HTTP/1.1" or "HTTP/2" (depends on server support)
```

HTTP/2 benefits: request multiplexing over a single TCP connection, header compression. Most useful for high-concurrency async workloads.
(source: httpx-http2.md)

## Event Hooks

Callbacks for cross-cutting concerns (logging, monitoring). Cannot mutate request/response (unlike `requests`).

```python
def log_request(request):
    print(f"→ {request.method} {request.url}")

def raise_on_4xx_5xx(response):
    response.read()  # body not read yet when hook fires
    response.raise_for_status()

client = httpx.Client(
    event_hooks={
        "request": [log_request],
        "response": [raise_on_4xx_5xx],
    }
)
```

For async clients, hooks must be async functions. For mutation or more control, use Custom Transports.
(source: httpx-advanced-event-hooks.md)

## Transports

Custom transport layer for testing, mocking, or direct WSGI/ASGI integration.

```python
# Mock transport for testing
def handler(request):
    return httpx.Response(200, json={"status": "ok"})

client = httpx.Client(transport=httpx.MockTransport(handler))

# WSGI transport (test Flask/Django without network)
transport = httpx.WSGITransport(app=flask_app)
client = httpx.Client(transport=transport)

# ASGI transport (test FastAPI/Starlette)
transport = httpx.ASGITransport(app=fastapi_app)
client = httpx.AsyncClient(transport=transport)
```

### Mounting Transports

Route different URLs to different transports:

```python
mounts = {
    "all://": httpx.HTTPTransport(proxy="http://proxy.example.com"),
    "all://*.internal.com": None,  # bypass proxy for internal
}
client = httpx.Client(mounts=mounts)
```

Routing patterns: `"all://"`, `"http://"`, `"https://"`, `"all://*.example.com"`, `"all://*:1234"`.
(source: httpx-advanced-transports.md)

## Extensions

Low-level request/response metadata. The `"trace"` extension exposes internal httpcore events:

```python
def log(event_name, info):
    print(event_name, info)

r = client.get("https://example.com", extensions={"trace": log})
```

Response extensions: `r.extensions["http_version"]` (bytes), `r.extensions["reason_phrase"]` (bytes), `r.extensions["network_stream"]` (raw socket access).
(source: httpx-advanced-extensions.md)

## Logging

Uses Python's standard `logging` module. Two loggers: `httpx` (high-level) and `httpcore` (network-level).

```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Now all httpx/httpcore debug output goes to console
```
(source: httpx-logging.md)

## Environment Variables

Respected when `trust_env=True` (default):

| Variable | Purpose |
|---|---|
| `HTTP_PROXY` | proxy for HTTP requests |
| `HTTPS_PROXY` | proxy for HTTPS requests |
| `ALL_PROXY` | proxy for all requests |
| `NO_PROXY` | comma-separated hostnames to bypass proxy |
| `SSL_CERT_FILE` | custom CA certificate file |
| `SSL_CERT_DIR` | custom CA certificate directory (requires `c_rehash`) |

Disable with `httpx.Client(trust_env=False)`.
(source: httpx-environment-variables.md)

## SSL Configuration

SSL verification is enabled by default (uses `certifi` CA bundle). Pass `verify=` on client instantiation, not per-request.

```python
# Disable verification (not recommended)
client = httpx.Client(verify=False)

# Custom CA bundle
import ssl
ctx = ssl.create_default_context(cafile="path/to/certs.pem")
client = httpx.Client(verify=ctx)

# System certificates (via truststore)
import truststore
ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
client = httpx.Client(verify=ctx)

# Client-side certificates
ctx = ssl.create_default_context()
ctx.load_cert_chain(certfile="path/to/client.pem")
client = httpx.Client(verify=ctx)
```

Different SSL configs require different Client instances.
(source: httpx-advanced-ssl.md)

## Text Encoding

Response decoding priority:
1. `Content-Type` charset from server
2. `default_encoding` parameter on Client (default: `"utf-8"`)
3. Auto-detection via callable

```python
# Explicit default
client = httpx.Client(default_encoding="shift_jis")

# Auto-detect with chardet
import chardet
client = httpx.Client(
    default_encoding=lambda content: chardet.detect(content).get("encoding", "utf-8")
)
```

Request body encoding: HTTPX uses UTF-8 (requests uses latin-1). For explicit encoding, pass bytes: `content="text".encode("latin-1")`.
(source: httpx-advanced-text-encodings.md, httpx-compatibility.md)

## Differences from requests

Key behavioral differences when migrating from `requests`:

| Feature | requests | httpx |
|---|---|---|
| Redirects | followed by default | **not** followed by default |
| Timeouts | none by default | 5 seconds by default |
| Session | `requests.Session` | `httpx.Client` |
| response.url | str | URL object |
| response.next | attribute | `response.next_request` |
| Raw content param | `data=<bytes>` | `content=<bytes>` |
| Success check | `response.is_ok` | `response.is_success` |
| Streaming | `stream=True` | `client.stream()` context manager |
| Proxy config | `proxies={"http": ...}` | `mounts={"http://": ...}` |
| Cookie mutation | per-request on session | client-level only |
| None params | omitted | **included** |
| Networking | urllib3 | httpcore |
| Top exception | `RequestException` | `HTTPError` |
| Mocking | responses, requests-mock | RESPX, pytest-httpx |
| Caching | cachecontrol, requests-cache | Hishel |

(source: httpx-compatibility.md)

## Third-Party Packages

Useful plugins:
- **httpx-retries** — retry layer (alternative to [[tenacity]] for simpler cases)
- **httpx-sse** — Server-Sent Events consumption
- **RESPX** / **pytest-httpx** — test mocking
- **Hishel** — HTTP caching
- **httpx-secure** — SSRF protection
- **httpx-ws** — WebSocket support
(source: httpx-third-party-packages.md)

## See Also

- [[tenacity]] — retry failed requests with backoff
- [[kalshi-api-auth]] — Kalshi RSA-PSS authentication
- [[kalshi-api-rate-limits]] — Kalshi rate limit tiers
- [[polymarket-us-api]] — Polymarket US API
- [[data-pipeline-stack]] — end-to-end data pull pattern
