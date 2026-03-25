"""
mood42 Simulation Server
FastAPI + SSE for real-time agent broadcasting
Now with geo-awareness: personalized content by viewer timezone
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Set, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from simulation import SimulationEngine
from channels import CHANNELS, TRACKS
from geo import get_region_from_offset, get_viewer_context, REGIONS


# SSE client connections - now keyed by channel:region
sse_clients: Dict[str, Set[asyncio.Queue]] = {
    "all": set(),
}
# Initialize for each channel:region combo
for ch_id in CHANNELS.keys():
    sse_clients[ch_id] = set()  # Channel-level (all regions)
    for region in REGIONS:
        sse_clients[f"{ch_id}:{region}"] = set()


async def broadcast(channel: str, event: str, data: dict):
    """Broadcast event to all SSE clients on a channel (or channel:region)."""
    message = f"event: {event}\ndata: {json.dumps(data)}\n\n"

    # Broadcast to specific channel:region subscribers
    if channel in sse_clients:
        dead_queues = []
        for queue in sse_clients[channel]:
            try:
                await queue.put(message)
            except:
                dead_queues.append(queue)
        for q in dead_queues:
            sse_clients[channel].discard(q)

    # If it's a region-specific channel (ch01:americas), also broadcast to channel-level
    if ":" in channel:
        base_channel = channel.split(":")[0]
        if base_channel in sse_clients:
            dead_queues = []
            for queue in sse_clients[base_channel]:
                try:
                    await queue.put(message)
                except:
                    dead_queues.append(queue)
            for q in dead_queues:
                sse_clients[base_channel].discard(q)

    # Also broadcast to "all" subscribers
    if channel != "all" and not channel.startswith("all:"):
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
    description="AI-programmed ambient TV channels with geo-awareness",
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
    return {"status": "ok", "time": datetime.now().isoformat(), "regions": REGIONS}


@app.get("/api/channels")
async def get_channels(tz: Optional[int] = Query(None, description="UTC offset in hours")):
    """Get all channel states for viewer's region."""
    region = get_region_from_offset(tz) if tz is not None else "americas"
    return {
        "channels": sim.get_all_channel_states(region),
        "world": sim.get_world_state(),
        "region": region,
    }


@app.get("/api/channels/{channel_id}")
async def get_channel(
    channel_id: str,
    tz: Optional[int] = Query(None, description="UTC offset in hours"),
):
    """Get single channel state with full agent details for viewer's region."""
    region = get_region_from_offset(tz) if tz is not None else "americas"
    state = sim.get_channel_state(channel_id, region)
    if not state:
        return {"error": "Channel not found"}, 404
    return state


@app.post("/api/channels/{channel_id}/join")
async def join_channel(
    channel_id: str,
    tz: Optional[int] = Query(None, description="UTC offset in hours"),
):
    """Increment viewer count for a channel in viewer's region."""
    region = get_region_from_offset(tz) if tz is not None else "americas"
    sim.increment_viewers(channel_id, region)

    agent = sim.channel_agents.get(channel_id)
    count = agent.get_region_state(region).viewer_count if agent else 0

    await broadcast(f"{channel_id}:{region}", "viewer:count", {
        "channelId": channel_id,
        "region": region,
        "count": count,
    })
    return {"ok": True, "region": region}


@app.post("/api/channels/{channel_id}/leave")
async def leave_channel(
    channel_id: str,
    tz: Optional[int] = Query(None, description="UTC offset in hours"),
):
    """Decrement viewer count for a channel in viewer's region."""
    region = get_region_from_offset(tz) if tz is not None else "americas"
    sim.decrement_viewers(channel_id, region)

    agent = sim.channel_agents.get(channel_id)
    count = agent.get_region_state(region).viewer_count if agent else 0

    await broadcast(f"{channel_id}:{region}", "viewer:count", {
        "channelId": channel_id,
        "region": region,
        "count": count,
    })
    return {"ok": True, "region": region}


@app.get("/api/viewer-context")
async def get_viewer_context_api(
    tz: Optional[int] = Query(None, description="UTC offset in hours"),
):
    """Get viewer context based on timezone."""
    region = get_region_from_offset(tz) if tz is not None else "americas"
    context = get_viewer_context(tz or 0)
    return context


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
async def stream_all(
    request: Request,
    tz: Optional[int] = Query(None, description="UTC offset in hours"),
):
    """SSE stream for all channel updates, personalized by region."""
    region = get_region_from_offset(tz) if tz is not None else "americas"

    queue = asyncio.Queue()
    sse_clients["all"].add(queue)

    async def cleanup():
        sse_clients["all"].discard(queue)

    # Send initial state for this region
    initial_data = {
        "channels": sim.get_all_channel_states(region),
        "world": sim.get_world_state(),
        "region": region,
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
async def stream_channel(
    channel_id: str,
    request: Request,
    tz: Optional[int] = Query(None, description="UTC offset in hours"),
):
    """SSE stream for single channel updates, personalized by region."""
    if channel_id not in CHANNELS:
        return {"error": "Channel not found"}, 404

    region = get_region_from_offset(tz) if tz is not None else "americas"
    channel_region_key = f"{channel_id}:{region}"

    # Ensure the key exists
    if channel_region_key not in sse_clients:
        sse_clients[channel_region_key] = set()

    queue = asyncio.Queue()
    sse_clients[channel_region_key].add(queue)

    async def cleanup():
        sse_clients[channel_region_key].discard(queue)

    # Send initial state for this region
    initial_data = sim.get_channel_state(channel_id, region)

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

# Serve static assets
app.mount("/assets", StaticFiles(directory=str(PROJECT_ROOT / "public" / "assets")), name="assets")

@app.get("/")
async def root():
    return FileResponse(str(PROJECT_ROOT / "index.html"))

@app.get("/favicon.svg")
async def favicon():
    return FileResponse(str(PROJECT_ROOT / "public" / "favicon.svg"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
