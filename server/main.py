"""
mood42 Simulation Server
FastAPI + SSE for real-time agent broadcasting
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from simulation import SimulationEngine
from channels import CHANNELS, TRACKS


# SSE client connections
sse_clients: Dict[str, Set[asyncio.Queue]] = {
    "all": set(),
}
for ch_id in CHANNELS.keys():
    sse_clients[ch_id] = set()


async def broadcast(channel: str, event: str, data: dict):
    """Broadcast event to all SSE clients on a channel."""
    message = f"event: {event}\ndata: {json.dumps(data)}\n\n"

    # Broadcast to specific channel subscribers
    if channel in sse_clients:
        dead_queues = []
        for queue in sse_clients[channel]:
            try:
                await queue.put(message)
            except:
                dead_queues.append(queue)
        for q in dead_queues:
            sse_clients[channel].discard(q)

    # Also broadcast to "all" subscribers
    if channel != "all":
        dead_queues = []
        for queue in sse_clients["all"]:
            try:
                await queue.put(message)
            except:
                dead_queues.append(queue)
        for q in dead_queues:
            sse_clients["all"].discard(q)


# Simulation engine instance
sim = SimulationEngine(broadcast_fn=broadcast)


async def simulation_loop():
    """Main simulation tick loop."""
    print("[Simulation] Starting tick loop...")
    while True:
        await sim.tick()
        await asyncio.sleep(5)  # 5 real seconds = 5 simulated minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Start simulation loop
    task = asyncio.create_task(simulation_loop())
    print("[Server] mood42 simulation server started")
    yield
    # Cleanup
    task.cancel()
    print("[Server] Shutting down...")


app = FastAPI(
    title="mood42 Simulation Server",
    description="AI-programmed ambient TV channels",
    lifespan=lifespan,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ API Routes ============

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "time": datetime.now().isoformat()}


@app.get("/api/channels")
async def get_channels():
    """Get all channel states."""
    return {
        "channels": sim.get_all_channel_states(),
        "world": sim.get_world_state(),
    }


@app.get("/api/channels/{channel_id}")
async def get_channel(channel_id: str):
    """Get single channel state with full agent details."""
    state = sim.get_channel_state(channel_id)
    if not state:
        return {"error": "Channel not found"}, 404
    return state


@app.post("/api/channels/{channel_id}/join")
async def join_channel(channel_id: str):
    """Increment viewer count for a channel."""
    sim.increment_viewers(channel_id)
    await broadcast(channel_id, "viewer:count", {
        "channelId": channel_id,
        "count": sim.agents[channel_id]["viewerCount"] if channel_id in sim.agents else 0
    })
    return {"ok": True}


@app.post("/api/channels/{channel_id}/leave")
async def leave_channel(channel_id: str):
    """Decrement viewer count for a channel."""
    sim.decrement_viewers(channel_id)
    await broadcast(channel_id, "viewer:count", {
        "channelId": channel_id,
        "count": sim.agents[channel_id]["viewerCount"] if channel_id in sim.agents else 0
    })
    return {"ok": True}


# ============ SSE Streams ============

async def event_generator(queue: asyncio.Queue):
    """Generate SSE events from queue."""
    try:
        while True:
            message = await queue.get()
            yield message
    except asyncio.CancelledError:
        pass


@app.get("/api/stream/all")
async def stream_all(request: Request):
    """SSE stream for all channel updates."""
    queue = asyncio.Queue()
    sse_clients["all"].add(queue)

    async def cleanup():
        sse_clients["all"].discard(queue)

    # Send initial state
    initial_data = {
        "channels": sim.get_all_channel_states(),
        "world": sim.get_world_state(),
    }

    async def generate():
        # Send initial state
        yield f"event: init\ndata: {json.dumps(initial_data)}\n\n"

        try:
            async for message in event_generator(queue):
                if await request.is_disconnected():
                    break
                yield message
        finally:
            await cleanup()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/stream/{channel_id}")
async def stream_channel(channel_id: str, request: Request):
    """SSE stream for single channel updates."""
    if channel_id not in CHANNELS:
        return {"error": "Channel not found"}, 404

    queue = asyncio.Queue()
    sse_clients[channel_id].add(queue)

    async def cleanup():
        sse_clients[channel_id].discard(queue)

    # Send initial state
    initial_data = sim.get_channel_state(channel_id)

    async def generate():
        # Send initial state
        yield f"event: init\ndata: {json.dumps(initial_data)}\n\n"

        try:
            async for message in event_generator(queue):
                if await request.is_disconnected():
                    break
                yield message
        finally:
            await cleanup()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ============ Static Files ============

import pathlib

# Get project root (parent of server directory)
PROJECT_ROOT = pathlib.Path(__file__).parent.parent

# Serve static files from public/assets directory
app.mount("/assets", StaticFiles(directory=str(PROJECT_ROOT / "public" / "assets")), name="assets")

# Serve index.html for root
@app.get("/")
async def root():
    return FileResponse(str(PROJECT_ROOT / "index.html"))

# Serve favicon
@app.get("/favicon.svg")
async def favicon():
    return FileResponse(str(PROJECT_ROOT / "public" / "favicon.svg"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
