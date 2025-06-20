
from uacp_sdk import Agent
import uuid, os
REG=os.getenv("REGISTRY_URL","http://localhost:8080")
agent=Agent("MembershipAgent", 8001, registry_url=REG)

@agent.register_tool("add_member", dict)
def add_member(*args):
        return {'member_id': 'M-'+uuid.uuid4().hex[:6]}

if __name__=="__main__":
    agent.run()
