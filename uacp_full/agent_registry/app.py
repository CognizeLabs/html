
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlmodel import SQLModel, Field, create_engine, Session, select
import json, datetime, hashlib, os, httpx

DB_URL = "sqlite:///data.db"
engine = create_engine(DB_URL, echo=False)

class Agent(SQLModel, table=True):
    agent_id: str = Field(primary_key=True)
    manifest:str
    jwks_uri:str
    manifest_hash:str
    last_seen: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class InAgent(BaseModel):
    agent_id:str; manifest:dict; jwks_uri:str

app = FastAPI(title="Agent Registry")

@app.on_event("startup")
def init(): SQLModel.metadata.create_all(engine)

@app.get("/agents", response_model=List[str])
def list_agents():
    with Session(engine) as s: return s.exec(select(Agent.agent_id)).all()

@app.get("/agents/{aid}")
def detail(aid:str):
    with Session(engine) as s:
        a=s.get(Agent,aid)
        if not a: raise HTTPException(404)
        return {"agent_id":a.agent_id,"manifest":json.loads(a.manifest),
                "jwks_uri":a.jwks_uri,"hash":a.manifest_hash}

@app.post("/onboard")
def onboard(data:InAgent):
    h=hashlib.sha256(json.dumps(data.manifest,separators=(',',':')).encode()).hexdigest()
    with Session(engine) as s:
        a=s.get(Agent,data.agent_id)
        if not a:
            a=Agent(agent_id=data.agent_id, manifest=json.dumps(data.manifest),
                    jwks_uri=data.jwks_uri, manifest_hash=h)
            s.add(a)
        else:
            a.manifest=json.dumps(data.manifest); a.jwks_uri=data.jwks_uri; a.manifest_hash=h
        s.commit()
    return {"status":"ok","hash":h}
