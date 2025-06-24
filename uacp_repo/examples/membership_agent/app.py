
from uacp_sdk import Agent
import os, uuid
REG = os.getenv("REGISTRY_URL", "http://localhost:8080")
agent = Agent("MembershipAgent", 8001, REG)

@agent.register_tool("add_member", dict)
def add_member(*args):
        return {'member_id': 'M-' + uuid.uuid4().hex[:6], 'status': 'created'}

if __name__ == "__main__":
    agent.run()
