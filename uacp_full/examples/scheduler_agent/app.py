
from uacp_sdk import Agent
import uuid, os
REG=os.getenv("REGISTRY_URL","http://localhost:8080")
agent=Agent("SchedulerAgent", 8002, registry_url=REG)

@agent.register_tool("book_appointment", str, str, str)
def book_appointment(*args):
        return {'confirmation_id':'A-'+uuid.uuid4().hex[:6]}

if __name__=="__main__":
    agent.run()
