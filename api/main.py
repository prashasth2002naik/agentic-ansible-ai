from fastapi import FastAPI
from agent.agent_controller import handle_request

app = FastAPI()

@app.post("/request-task")
def request_task(payload: dict):
    return handle_request(
        payload.get("text"),
        payload.get("credentials")
    )
