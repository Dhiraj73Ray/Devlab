import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from engine import list_recipes, list_workspaces, create_project

app = FastAPI(title="DevLab")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CreateRequest(BaseModel):
    recipe: str
    project_name: str

@app.get("/api/recipes")
def get_recipes():
    return list_recipes()

@app.get("/api/workspaces")
def get_workspaces():
    return list_workspaces()

@app.post("/api/projects")
async def post_project(req: CreateRequest):
    try:
        path = await asyncio.to_thread(create_project, req.recipe, req.project_name)
        return {"path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.websocket("/ws/create")
async def ws_create(ws: WebSocket):
    await ws.accept()
    try:
        payload = await ws.receive_json()
        recipe = payload["recipe"]
        project_name = payload["project_name"]

        loop = asyncio.get_running_loop()

        def log(line: str):
            asyncio.run_coroutine_threadsafe(ws.send_text(line), loop)

        await asyncio.to_thread(create_project, recipe, project_name, log)
        await ws.send_text("__DONE__")
    except WebSocketDisconnect:
        return
    except Exception as e:
        await ws.send_text(f"__ERROR__ {e}")
    finally:
        await ws.close()