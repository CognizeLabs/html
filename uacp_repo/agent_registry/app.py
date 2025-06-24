
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os, hashlib, datetime, json

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB", "uacp")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]
agents = db.agents

class AgentIn(BaseModel):
    agent_id: str
    manifest: dict
    jwks_uri: str

app = FastAPI(title="U-ACP Agent Registry (Mongo)")

@app.get("/agents")
async def list_agents():
    cursor = agents.find({}, {"_id":0, "agent_id":1})
    return [doc async for doc in cursor]

@app.get("/agents/{aid}")
async def detail(aid: str):
    doc = await agents.find_one({"agent_id": aid}, {"_id":0})
    if not doc:
        raise HTTPException(404)
    return doc

@app.post("/onboard")
async def onboard(data: AgentIn):
    mhash = hashlib.sha256(json.dumps(data.manifest, separators=(',',':')).encode()).hexdigest()
    doc = {
        "agent_id": data.agent_id,
        "manifest": data.manifest,
        "jwks_uri": data.jwks_uri,
        "manifest_hash": mhash,
        "last_seen": datetime.datetime.utcnow()
    }
    await agents.update_one({"agent_id": data.agent_id}, {"$set": doc}, upsert=True)
    return {"status": "ok", "hash": mhash}
