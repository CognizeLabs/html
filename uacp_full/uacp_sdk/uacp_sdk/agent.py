
import time, uuid, json, pathlib, base64, math, logging
from typing import Dict, Tuple, Callable, Any
import jwt, httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

log = logging.getLogger("uacp_sdk")
JSONRPC = "2.0"
TTL = 300
KEY_DIR = pathlib.Path("/keys")
KEY_DIR.mkdir(exist_ok=True, parents=True)

def _p(agent, suf): return KEY_DIR / f"{agent}_{suf}"

def _ensure_keys(aid:str):
    if _p(aid,"private.pem").exists(): return
    k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _p(aid,"private.pem").write_bytes(k.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()))
    _p(aid,"public.pem").write_bytes(k.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo))
    # jwks
    n,e = k.public_key().public_numbers().n, k.public_key().public_numbers().e
    b64 = lambda i: base64.urlsafe_b64encode(i.to_bytes(math.ceil(i.bit_length()/8),"big")).rstrip(b"=").decode()
    jwk = {"kty":"RSA","alg":"RS256","use":"sig","kid":f"{aid}-key1","n":b64(n),"e":b64(e)}
    _p(aid,"jwks.json").write_text(json.dumps({"keys":[jwk]}, indent=2))

def _priv(aid): _ensure_keys(aid); return _p(aid,"private.pem").read_text()
def create_jwt(aid, scope, aud):
    return jwt.encode({"sub":aid,"aud":aud,"iat":int(time.time()),"exp":int(time.time())+TTL,"jti":uuid.uuid4().hex,"scope":scope},
                      _priv(aid),algorithm="RS256",headers={"kid":f"{aid}-key1"})

class RPCReq(BaseModel):
    jsonrpc:str=Field(JSONRPC,const=True)
    id:str; method:str; params:Any|None=None; kind:str="tool"; nonce:str; iat:int; scope:str; auth:str

class RPCRes(BaseModel):
    jsonrpc:str=Field(JSONRPC,const=True)
    id:str; result:Any|None=None; error:str|None=None

class Agent:
    def __init__(self, aid:str, port:int, registry_url:str):
        self.id, self.port, self.registry = aid, port, registry_url
        _ensure_keys(aid)
        self.app=FastAPI(title=aid)
        self.tools:Dict[str,Tuple[Callable,Tuple[type,...]]]={}
        self.nonces:set[str]=set(); self._routes()
    def register_tool(self,name,*sig):
        def dec(fn): self.tools[name]=(fn,sig); return fn
        return dec
    def _manifest(self): return {"agent_id":self.id,
            "jwks_uri":f"http://{self.id.lower()}:{self.port}/.well-known/jwks.json",
            "tools":{k:{"params":[t.__name__ for t in s],"scope":f"tool:{k}"} for k,(f,s) in self.tools.items()}}
    def _routes(self):
        @self.app.on_event("startup")
        async def onboard():
            try:
                httpx.post(f"{self.registry}/onboard",json={"agent_id":self.id,"manifest":self._manifest(),
                                                            "jwks_uri":self._manifest()["jwks_uri"]},timeout=5)
            except Exception as exc:
                log.warning("registry unreachable: %s", exc)
        @self.app.post("/rpc")
        async def rpc(req:Request):
            body=await req.json(); r=RPCReq(**body)
            if r.nonce in self.nonces: raise HTTPException(409,"replay")
            self.nonces.add(r.nonce)
            if r.method not in self.tools: return RPCRes(id=r.id,error="unknown").dict()
            fn,sig=self.tools[r.method]; p=r.params or []
            if not isinstance(p,(list,tuple)): p=[p]
            return RPCRes(id=r.id,result=fn(*p)).dict()
        @self.app.get("/.well-known/agent.json")
        def manif(): return self._manifest()
        @self.app.get("/.well-known/jwks.json")
        def jwks(): return FileResponse(_p(self.id,"jwks.json"))
    def run(self):
        import uvicorn; uvicorn.run(self.app,host="0.0.0.0",port=self.port,log_level="warning")
