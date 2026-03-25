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

from server.simulation import SimulationEngine
from server.channels import CHANNELS, TRACKS
from server.geo import get_region_from_offset, get_viewer_context, REGIONS
from server.tools import _verified_urls, _broken_urls, check_url_health


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


@app.get("/api/ops")
async def ops_dashboard():
    """Internal ops dashboard - monitor all agents across all regions."""
    import time
    now = int(time.time() * 1000)

    ops_data = {
        "server_time": datetime.now().isoformat(),
        "tick": sim.world["tick"],
        "uptime_ticks": sim.world["tick"],
        "regions": REGIONS,
        "channels": [],
    }

    for ch_id, channel in CHANNELS.items():
        agent = sim.channel_agents.get(ch_id)
        if not agent:
            continue

        channel_data = {
            "id": ch_id,
            "name": channel["name"],
            "agent_name": channel["agent"]["name"],
            "energy": agent.energy,
            "regions": {},
        }

        for region in REGIONS:
            region_state = agent.get_region_state(region)
            track = region_state.current_track

            # Calculate staleness
            if track and region_state.last_track_change:
                elapsed_ms = now - region_state.last_track_change
                elapsed_min = elapsed_ms / 60000
                duration_min = track.get("duration", 180) / 60
                is_stale = elapsed_min > (duration_min + 1)  # Stale if over duration + 1 min
            else:
                elapsed_min = 0
                is_stale = track is None

            video = region_state.current_video
            channel_data["regions"][region] = {
                "track": track["name"] if track else None,
                "track_id": track["id"] if track else None,
                "track_url": track["url"] if track else None,
                "video": video["name"] if video else None,
                "video_url": video["url"] if video else None,
                "mood": region_state.current_mood,
                "viewers": region_state.viewer_count,
                "local_time": region_state.local_time,
                "elapsed_min": round(elapsed_min, 1),
                "is_stale": is_stale,
                "status": "broken" if track is None else ("stale" if is_stale else "ok"),
            }

        channel_data["all_ok"] = all(
            r["status"] == "ok" for r in channel_data["regions"].values()
        )
        ops_data["channels"].append(channel_data)

    # Summary stats
    total_streams = len(ops_data["channels"]) * len(REGIONS)
    ok_streams = sum(
        1 for ch in ops_data["channels"]
        for r in ch["regions"].values()
        if r["status"] == "ok"
    )
    broken_streams = sum(
        1 for ch in ops_data["channels"]
        for r in ch["regions"].values()
        if r["status"] == "broken"
    )

    ops_data["summary"] = {
        "total_streams": total_streams,
        "ok": ok_streams,
        "stale": total_streams - ok_streams - broken_streams,
        "broken": broken_streams,
        "health_pct": round(ok_streams / total_streams * 100, 1) if total_streams > 0 else 0,
    }

    # URL validation stats
    ops_data["url_health"] = {
        "verified_count": len(_verified_urls),
        "broken_count": len(_broken_urls),
        "verified_urls": list(_verified_urls)[:10],  # Show first 10
        "broken_urls": list(_broken_urls.keys())[:10],
    }

    return ops_data


@app.get("/api/ops/test-url")
async def test_url(url: str):
    """Test if a URL is accessible."""
    is_valid = await check_url_health(url)
    return {
        "url": url,
        "valid": is_valid,
        "verified_count": len(_verified_urls),
        "broken_count": len(_broken_urls),
    }


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


@app.get("/ops")
async def ops_page():
    """Internal ops dashboard page."""
    return FileResponse(str(PROJECT_ROOT / "public" / "ops.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
