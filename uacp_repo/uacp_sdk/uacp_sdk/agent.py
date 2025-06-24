
import time, uuid, json, pathlib, base64, math, logging
from typing import Dict, Tuple, Callable, Any

import jwt, httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

JSONRPC = "2.0"
TTL = 300
KEY_DIR = pathlib.Path("/keys")
KEY_DIR.mkdir(parents=True, exist_ok=True)
log = logging.getLogger("uacp_sdk")

# --- key helpers -----------------------------------------------------
def _kpath(a, suf): return KEY_DIR / f"{a}_{suf}"

def _ensure_keys(aid: str):
    if _kpath(aid, 'private.pem').exists(): return
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _kpath(aid, 'private.pem').write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    _kpath(aid, 'public.pem').write_bytes(
        key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    n, e = key.public_key().public_numbers()
    b64 = lambda i: base64.urlsafe_b64encode(i.to_bytes(math.ceil(i.bit_length()/8),'big')).rstrip(b'=').decode()
    jwk = {"kty":"RSA","alg":"RS256","use":"sig","kid":f"{aid}-key1","n":b64(n),"e":b64(e)}
    _kpath(aid, 'jwks.json').write_text(json.dumps({"keys":[jwk]}, indent=2))

def _priv(a): _ensure_keys(a); return _kpath(a, 'private.pem').read_text()

def create_jwt(sub: str, scope: str, aud: str) -> str:
    payload = {
        "sub": sub, "aud": aud,
        "iat": int(time.time()),
        "exp": int(time.time()) + TTL,
        "jti": uuid.uuid4().hex,
        "scope": scope
    }
    return jwt.encode(payload, _priv(sub), algorithm="RS256", headers={"kid": f"{sub}-key1"})

# --- pydantic models ---------------------------------------------------
class RPCRequest(BaseModel):
    jsonrpc: str = Field(JSONRPC, const=True)
    id: str
    method: str
    params: Any | None = None
    kind: str = "tool"
    nonce: str
    iat: int
    scope: str
    auth: str

class RPCResponse(BaseModel):
    jsonrpc: str = Field(JSONRPC, const=True)
    id: str
    result: Any | None = None
    error: str | None = None

# --- Agent runtime -----------------------------------------------------
class Agent:
    def __init__(self, agent_id: str, port: int, registry_url: str):
        self.id = agent_id
        self.port = port
        self.registry = registry_url
        _ensure_keys(agent_id)

        self.app = FastAPI(title=agent_id)
        self.tools: Dict[str, Tuple[Callable, Tuple[type, ...]]] = {}
        self.nonces: set[str] = set()
        self._setup_routes()

    # decorator
    def register_tool(self, name: str, *sig: type):
        def wrapper(fn):
            self.tools[name] = (fn, sig)
            return fn
        return wrapper

    # manifest
    def _manifest(self) -> dict:
        return {
            "agent_id": self.id,
            "jwks_uri": f"http://{self.id.lower()}:{self.port}/.well-known/jwks.json",
            "tools": {
                k: {
                    "params": [t.__name__ for t in sig],
                    "scope": f"tool:{k}"
                } for k, (_, sig) in self.tools.items()
            }
        }

    # routes
    def _setup_routes(self):
        @self.app.on_event("startup")
        async def _register():
            try:
                httpx.post(f"{self.registry}/onboard", json={
                    "agent_id": self.id,
                    "manifest": self._manifest(),
                    "jwks_uri": self._manifest()["jwks_uri"]
                }, timeout=8)
            except Exception as exc:
                log.warning("Registry not reachable: %s", exc)

        @self.app.post("/rpc")
        async def _rpc(req: Request):
            data = await req.json()
            r = RPCRequest(**data)
            if r.nonce in self.nonces:
                raise HTTPException(409, "replay")
            self.nonces.add(r.nonce)

            if r.method not in self.tools:
                return RPCResponse(id=r.id, error="unknown method").dict()

            fn, sig = self.tools[r.method]
            p = r.params or []
            if not isinstance(p, (list, tuple)):
                p = [p]
            return RPCResponse(id=r.id, result=fn(*p)).dict()

        # discovery routes
        @self.app.get("/.well-known/agent.json")
        async def manifest():
            return self._manifest()

        @self.app.get("/.well-known/jwks.json")
        async def jwks():
            return FileResponse(_kpath(self.id, 'jwks.json'))

    def run(self):
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="info")
