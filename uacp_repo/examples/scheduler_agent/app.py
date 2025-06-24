
from uacp_sdk import Agent
import os, uuid
REG = os.getenv("REGISTRY_URL", "http://localhost:8080")
agent = Agent("SchedulerAgent", 8002, REG)

@agent.register_tool("book_appointment", str, str, str)
def book_appointment(*args):
        return {'confirmation_id': 'A-' + uuid.uuid4().hex[:6]}

if __name__ == "__main__":
    agent.run()
