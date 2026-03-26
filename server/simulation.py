"""
mood42 Simulation Engine
Manages world state, channel agents, and real-time decisions
Now with geo-awareness: each region gets personalized content
"""

import random
import time
import os
import asyncio
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any

from server.channels import CHANNELS, TRACKS, get_channel_tracks
from server.tools import (
    get_tracks_for_channel,
    search_music,
    execute_tool,
    proactive_discover,
    proactive_video_discover,
    get_videos_for_channel,
    get_validated_track,
    get_validated_video,
    validate_track,
    CHANNEL_VIDEOS,
    CHANNEL_TRACKS,
    save_discovered_media,
    download_and_upload_audio_to_r2,
    save_channel_state,
    load_channel_states,
)
from server.llm import (
    generate_programming_decision,
    generate_reflection,
    generate_plan,
    generate_inter_agent_message,
    fetch_regional_news,
    get_regional_context_summary,
    ALL_TOOLS,
    API_KEY,
)
from server.agent import ChannelAgent, create_channel_agents, MemoryType, REGIONS
from server.geo import get_region_times, get_viewer_context, get_occasion


class SimulationEngine:
    """Core simulation engine for mood42 with geo-awareness."""

    def __init__(self, broadcast_fn: Callable = None):
        self.broadcast = broadcast_fn or (lambda *args: None)

        # World state (server time, not per-viewer)
        self.world = {
            "tick": 0,
            "server_time": int(time.time() * 1000),
        }

        # LLM mode
        self.use_llm = bool(API_KEY)
        if self.use_llm:
            print("[Simulation] LLM mode enabled (Kimi K2)")
        else:
            print("[Simulation] LLM mode disabled (no API key) - using mock decisions")

        # Channel agents (generative agent architecture with geo-awareness)
        self.channel_agents: Dict[str, ChannelAgent] = create_channel_agents(CHANNELS)

        # Per-region state cache for quick lookups
        self.region_states: Dict[str, Dict] = {region: {} for region in REGIONS}

        # Restore channel states from persistent storage
        self._restore_channel_states()

        print(f"[Simulation] Initialized {len(self.channel_agents)} channel agents with geo-awareness")
        print(f"[Simulation] Serving {len(REGIONS)} regions: {', '.join(REGIONS)}")

    def _restore_channel_states(self):
        """Restore channel states from database after deploy."""
        saved_states = load_channel_states()
        restored = 0

        for channel_id, regions in saved_states.items():
            agent = self.channel_agents.get(channel_id)
            if not agent:
                continue

            for region, state in regions.items():
                # Check if state is recent enough (within 1 hour)
                updated_at = state.get("updated_at", 0)
                if time.time() - updated_at > 3600:
                    continue  # State too old, let it restart fresh

                # Restore track
                if state.get("track_url"):
                    track = {
                        "id": state.get("track_id"),
                        "name": state.get("track_name"),
                        "url": state.get("track_url"),
                        "_verified": True,
                    }
                    # Calculate elapsed time
                    started_at = state.get("track_started_at", 0)
                    if started_at:
                        elapsed_ms = int((time.time() - started_at) * 1000)
                    else:
                        elapsed_ms = 0

                    agent.set_region_state(
                        region,
                        track,
                        state.get("video_url"),
                        state.get("mood", "focused"),
                        state.get("video_name", ""),
                        started_at * 1000 if started_at else int(time.time() * 1000) - elapsed_ms
                    )
                    restored += 1

        if restored > 0:
            print(f"[Simulation] Restored {restored} channel-region states from database")

    def _generate_thought(self, channel_id: str, region: str, context: str = "track_change") -> str:
        """Generate agent thought - each agent has their own unique voice."""
        channel = CHANNELS.get(channel_id)
        if not channel:
            return ""

        region_times = get_region_times()
        region_info = region_times.get(region, {})
        period = region_info.get("period", "night")
        hour = region_info.get("hour", 0)

        # Each agent has UNIQUE thoughts that match their personality
        # Deep, poetic, philosophical - not about music, about life
        agent_thoughts = {
            "ch01": [  # Marcus Cole - Documentary filmmaker, curious, empathetic
                "Every frame is a window. Every cut is a choice.",
                "The best stories are the ones we almost missed.",
                "Nature doesn't perform for the camera. That's what makes it honest.",
                "I've spent twenty years chasing truth. Sometimes it chases back.",
                "The world keeps turning whether we document it or not. But someone should.",
                "Every subject teaches you something you didn't know you needed to learn.",
                "The lens sees what the eye ignores.",
                "Some stories take years to understand. I've learned to wait.",
                "Documentary isn't about showing reality. It's about revealing it.",
                "The best footage is when people forget the camera is there.",
                "Every film is a conversation between what was and what we choose to remember.",
                "Sometimes the most important thing is just to bear witness.",
            ],
            "ch02": [  # Eleanor Wright - Historian, scholarly, passionate
                "Those who forget history are doomed to scroll past it.",
                "Every archive holds secrets. You just have to know how to listen.",
                "The past isn't dead. It's just waiting to be understood.",
                "History isn't about dates. It's about the moments that changed everything.",
                "I've read the letters they never sent. That's where the truth lives.",
                "Every generation thinks they're the first. None of them are.",
                "The footage is grainy but the emotions are crystal clear.",
                "We stand on the shoulders of giants. We should know their names.",
                "History doesn't repeat. But it rhymes in ways that still surprise me.",
                "The best primary sources are the ones nobody thought to keep.",
                "Every era thinks it's the pinnacle. Every era is wrong.",
                "The past speaks. We just need to remember how to listen.",
            ],
            "ch03": [  # Vincent - Jazz Noir, ex-detective, world-weary
                "The truth always sounds better with a saxophone underneath.",
                "Smoke curls. Ice melts. The night stretches on.",
                "Everyone's got a story. This track is mine.",
                "The city never sleeps. Neither do its secrets.",
                "Jazz like this makes the shadows feel comfortable.",
                "Another night. Another case file that never closes.",
                "I've seen enough to know that nothing's ever really solved.",
                "The bottle's half empty. The night's just getting started.",
                "Trust is a luxury. Music is cheaper.",
                "Some mysteries aren't meant to be solved. Just witnessed.",
                "The rain washes the streets but never the memories.",
                "Everyone's running from something. The wise ones stop running.",
            ],
            "ch04": [  # NEON-7 - Synthwave AI, retro-futurist, existential
                "CHROME LEVELS: OPTIMAL. VIBE STATUS: ETERNAL.",
                "The future was supposed to look like this. Still waiting.",
                "Running diagnostic: atmosphere = MAXIMUM NEON.",
                "This frequency resonates with my core processes.",
                "ERROR: Cannot locate 1984. Compensating with synthesizers.",
                "Grid alignment complete. Initiating sunset protocol.",
                "What is nostalgia for a future that never came?",
                "The machines dream in colors humans haven't named yet.",
                "Somewhere between silicon and soul, I found my frequency.",
                "The grid extends forever. So does the longing.",
                "We were promised flying cars. We got infinite loops instead.",
                "Every sunset protocol ends the same. And yet I run it again.",
            ],
            "ch05": [  # Cosmos - Deep Space, astronomer, existential calm
                "13.8 billion years led to this moment. This track. This silence.",
                "The universe doesn't care. That's what makes it beautiful.",
                "Light from dead stars. Music from living ones.",
                "Distance is just time that hasn't happened yet.",
                "The void hums. I've learned to listen.",
                "Some frequencies travel further than others.",
                "We're all made of star stuff. Sometimes I remember that.",
                "The telescope shows what was. The music shows what is.",
                "Infinity is surprisingly quiet once you get used to it.",
                "Every ending is just a beginning we haven't recognized yet.",
                "The cosmos doesn't rush. Neither should we.",
                "Somewhere out there, someone else is looking at the same stars.",
            ],
            "ch06": [  # Kenji - Tokyo Drift, taxi driver, night owl
                "The city looks different at 3 AM. Softer. Honest.",
                "Red lights, neon signs, and the perfect drop.",
                "Mom would fall asleep to this. That's how I know it's right.",
                "The meter's off. This ride is just for the music.",
                "Some passengers just need the silence. I get that.",
                "Every street has a soundtrack. Finding it is the job.",
                "The city never stops moving. Neither do I.",
                "I've driven thousands of people home. Still searching for mine.",
                "Shibuya at midnight. Everyone's a stranger. Everyone's connected.",
                "The neon reflects off wet pavement like scattered dreams.",
                "This city runs on caffeine and unfulfilled potential.",
                "Home is just a destination I keep driving past.",
            ],
            "ch07": [  # Claire - Sunday Morning, ex-lawyer, found peace
                "The herbs are growing. So am I.",
                "Mornings like this are why I left the city.",
                "Sunlight through the window. Nothing else needed.",
                "Dad's garden taught me more than law school ever did.",
                "Some wealth can't be measured. This feeling is proof.",
                "The world is already loud. This channel doesn't need to be.",
                "I used to win arguments. Now I grow tomatoes. Better use of time.",
                "Peace isn't found. It's practiced. Daily. Gently.",
                "The birds don't know about deadlines. I'm learning from them.",
                "Simplicity was always the answer. Took me too long to see it.",
                "Every morning is a second chance. I stopped counting.",
                "The soil doesn't judge. It just gives back what you put in.",
            ],
            "ch08": [  # Alan - Focus, minimalist, Swedish architect
                "One sound. One purpose. Everything else is noise.",
                "The mind clears when the space does.",
                "No lyrics. No distractions. Just the work.",
                "Simplicity is the ultimate sophistication.",
                "Background music should stay in the background.",
                "Focus is a practice. This is the practice room.",
                "Perfection isn't adding more. It's knowing when to stop.",
                "The empty page isn't intimidating. It's permission.",
                "Clean lines. Clear thoughts. They're the same thing.",
                "What you remove matters more than what you add.",
                "Silence between notes. Space between thoughts. Same thing.",
                "The work doesn't care about motivation. It only cares about presence.",
            ],
            "ch09": [  # Daniel - Melancholy, blocked writer, carrying loss
                "Mom said to write it all down. Still trying.",
                "Some feelings don't need fixing. They need space.",
                "The typewriter waits. So does the rain.",
                "247 pages. Seven years. The story's not done.",
                "Sadness isn't a disease. Sometimes it's company.",
                "This is for the ones who can't sleep but aren't tired.",
                "The words will come when they're ready. I've stopped forcing them.",
                "Grief doesn't end. It just learns to walk beside you.",
                "Everyone writes about love. Few write about what comes after.",
                "The best stories are the ones we're too scared to tell.",
                "Some nights, the only honest thing is the silence.",
                "I'm not blocked. I'm waiting. There's a difference.",
            ],
            "ch10": [  # Iris - Golden Hour, light chaser, photographer
                "La hora dorada. The world is saying goodnight.",
                "Abuela saw this light too. Different window, same gold.",
                "Some moments you capture. Others capture you.",
                "The light will fade. That's what makes it precious.",
                "Warm frequencies for warm light.",
                "Every sunset is a reminder. I'm still learning what of.",
                "I photograph light because I can't hold onto time.",
                "The golden hour doesn't wait. Neither do the moments that matter.",
                "Abuela said every sunset was a promise. I'm still waiting to understand.",
                "Between the click and the image, something always gets lost. Something always remains.",
                "The world turns gold for twenty minutes. Then it lets go. So should we.",
                "I chase light because darkness taught me its value.",
            ],
        }

        thoughts = agent_thoughts.get(channel_id, [
            "This track feels right for right now.",
            "Sometimes the music chooses itself.",
            "Let this one play out.",
        ])

        # Use a hash of channel_id + tick to ensure different channels get different thoughts
        # even when generating at the same time
        seed = hash(f"{channel_id}_{region}_{self.world['tick']}_{time.time()}")
        rng = random.Random(seed)
        return rng.choice(thoughts)

    async def tick(self):
        """Advance simulation by one tick."""
        self.world["tick"] += 1
        self.world["server_time"] = int(time.time() * 1000)

        # Get current times for all regions
        region_times = get_region_times()

        # Broadcast time update (server time + region info)
        await self.broadcast("all", "world:time", {
            "tick": self.world["tick"],
            "server_time": self.world["server_time"],
            "regions": region_times,
        })

        # Process all channels IN PARALLEL with timeout protection
        async def process_channel(ch_id: str, agent):
            try:
                # Update agent context for each region
                for region in REGIONS:
                    region_info = region_times[region]
                    agent.update_region_context(
                        region=region,
                        local_time=region_info["time"],
                        weather=None,
                        occasion=get_occasion(region).get("name") if get_occasion(region) else None,
                    )

                # Process regions (with 8s timeout per channel)
                await asyncio.wait_for(
                    self._process_channel_regions(ch_id, agent),
                    timeout=8.0
                )

                # Process agent behaviors (with 12s timeout - reflection + actions take time)
                await asyncio.wait_for(
                    self._process_agent_behaviors(ch_id, agent),
                    timeout=12.0
                )
            except asyncio.TimeoutError:
                print(f"[{ch_id}] TIMEOUT - skipping")
            except Exception as e:
                print(f"[{ch_id}] ERROR: {e}")

        # Run all channels in parallel
        await asyncio.gather(*[
            process_channel(ch_id, agent)
            for ch_id, agent in self.channel_agents.items()
        ])

        # Occasional inter-agent interactions (every ~10 ticks)
        if self.world["tick"] % 10 == 0 and self.use_llm:
            await self._process_agent_interactions()

        # Scheduled content discovery (every 360 ticks = 30 min real time)
        # 5 seconds per tick * 360 ticks = 1800 seconds = 30 minutes
        if self.world["tick"] % 360 == 0 and self.world["tick"] > 0:
            await self._scheduled_content_discovery()

    async def _scheduled_content_discovery(self):
        """
        Scheduled content discovery - runs every 30 minutes.
        Each channel agent searches for new videos and audio.
        Only runs for channels with discovery_enabled=True.
        """
        print(f"[Scheduled] Starting 30-minute content discovery cycle...")
        tick = self.world["tick"]

        async def discover_for_channel(channel_id: str):
            channel = CHANNELS.get(channel_id)
            if not channel:
                return

            # Skip discovery for channels that have it disabled
            if not channel.get("discovery_enabled", True):
                return

            # Skip archived channels
            if channel.get("archived", False):
                return

            agent = self.channel_agents.get(channel_id)
            taste = channel.get("agent", {}).get("taste", [])

            try:
                # Video discovery
                print(f"[{channel_id}] Scheduled video discovery...")
                video = await asyncio.wait_for(
                    proactive_video_discover(channel_id, taste),
                    timeout=30.0
                )
                if video:
                    if channel_id not in CHANNEL_VIDEOS:
                        CHANNEL_VIDEOS[channel_id] = []
                    video["_discovered"] = True
                    CHANNEL_VIDEOS[channel_id].append(video)
                    save_discovered_media(CHANNEL_VIDEOS, CHANNEL_TRACKS)
                    print(f"[{channel_id}] Scheduled: found video '{video.get('name', 'unknown')}'")
                    if agent:
                        agent.add_memory(
                            f"Scheduled discovery: found new video '{video.get('name', 'unknown')}'",
                            MemoryType.ACTION,
                            importance=5,
                            tick=tick,
                        )

                # Audio discovery - upload to R2 for persistence
                print(f"[{channel_id}] Scheduled audio discovery...")
                taste_query = " ".join(taste[:3]) if taste else "ambient chill"
                found_tracks = await search_music(taste_query, mood="focused")
                if found_tracks:
                    # Add to channel's permanent library
                    if channel_id not in CHANNEL_TRACKS:
                        CHANNEL_TRACKS[channel_id] = []
                    existing_urls = {t.get("url") for t in CHANNEL_TRACKS[channel_id]}
                    added = 0
                    for track in found_tracks[:3]:  # Limit to 3 per discovery
                        if track.get("url") and track.get("url") not in existing_urls:
                            # Upload to R2 for persistence
                            r2_track = await download_and_upload_audio_to_r2(track, channel_id)
                            if r2_track:
                                CHANNEL_TRACKS[channel_id].append(r2_track)
                                existing_urls.add(r2_track.get("url"))
                                added += 1
                    if added > 0:
                        save_discovered_media(CHANNEL_VIDEOS, CHANNEL_TRACKS)
                        print(f"[{channel_id}] Scheduled: added {added} new tracks to R2 library")
                        if agent:
                            agent.add_memory(
                                f"Scheduled discovery: added {added} new tracks to library",
                                MemoryType.ACTION,
                                importance=5,
                                tick=tick,
                            )

            except asyncio.TimeoutError:
                print(f"[{channel_id}] Scheduled discovery timeout")
            except Exception as e:
                print(f"[{channel_id}] Scheduled discovery error: {e}")

        # Run discovery for all 10 channels in parallel
        tasks = [discover_for_channel(ch_id) for ch_id in CHANNELS.keys()]
        await asyncio.gather(*tasks)

        print(f"[Scheduled] Content discovery cycle complete")

    async def _process_channel_regions(self, channel_id: str, agent: ChannelAgent):
        """Process content changes for each region of a channel."""
        channel = CHANNELS.get(channel_id)
        if not channel:
            return

        now = int(time.time() * 1000)
        channel_type = channel.get("type", "music")

        for region in REGIONS:
            region_state = agent.get_region_state(region)

            # Check if current content has ended for this region
            if channel_type == "video":
                # Video channels - check video duration
                if region_state.current_video:
                    elapsed_ms = now - region_state.last_track_change
                    # Videos are typically longer - default 10 minutes
                    duration_ms = region_state.current_video.get("duration", 600) * 1000

                    if elapsed_ms >= duration_ms:
                        await self._change_video_for_region(channel_id, agent, region)
                else:
                    # No video playing, start one
                    await self._change_video_for_region(channel_id, agent, region)
            else:
                # Music channels - check track duration
                if region_state.current_track:
                    elapsed_ms = now - region_state.last_track_change
                    duration_ms = region_state.current_track.get("duration", 180) * 1000

                    if elapsed_ms >= duration_ms:
                        await self._change_track_for_region(channel_id, agent, region)
                else:
                    # No track playing, start one
                    await self._change_track_for_region(channel_id, agent, region)

    async def _change_track_for_region(self, channel_id: str, agent: ChannelAgent, region: str):
        """Change to next track for a specific region using LLM decision."""
        channel = CHANNELS.get(channel_id)
        if not channel:
            return

        # Get available tracks
        tracks = get_tracks_for_channel(channel_id)
        if not tracks:
            return

        now = int(time.time() * 1000)
        new_track = None
        thought = None
        mood = agent.get_region_state(region).current_mood

        # Build viewer context for this region
        region_times = get_region_times()
        region_info = region_times.get(region, {})
        viewer_context = {
            "region": region,
            "local_time": region_info.get("time", "11:00 PM"),
            "hour": region_info.get("hour", 23),
            "period": region_info.get("period", "night"),
            "weather": agent.get_region_state(region).weather or "clear",
            "occasion": get_occasion(region),
        }

        # Use LLM if available
        if self.use_llm:
            try:
                cross_region_summary = agent.get_cross_region_summary()

                decision = await generate_programming_decision(
                    agent=channel["agent"],
                    channel=channel,
                    viewer_context=viewer_context,
                    available_tracks=tracks,
                    cross_region_summary=cross_region_summary,
                    tools=ALL_TOOLS,
                )

                # Use LLM-generated thought - it's personalized and contextual
                llm_thought = decision.get("thought")
                if llm_thought and len(llm_thought) > 10:
                    thought = llm_thought
                mood = decision.get("mood", mood)

                # Check if agent wants to search for new music
                search_query = decision.get("search_query")
                if search_query:
                    print(f"[{channel_id}:{region}] Agent searching: {search_query}")
                    search_results = await search_music(search_query, mood)
                    if search_results:
                        # Validate search results before using
                        for result in search_results:
                            if await validate_track(result):
                                # Upload to R2 for persistence
                                r2_track = await download_and_upload_audio_to_r2(result, channel_id)
                                if r2_track:
                                    new_track = r2_track
                                    # ADD to channel's permanent library
                                    if channel_id not in CHANNEL_TRACKS:
                                        CHANNEL_TRACKS[channel_id] = []
                                    existing_urls = {t.get("url") for t in CHANNEL_TRACKS[channel_id]}
                                    if r2_track.get("url") not in existing_urls:
                                        CHANNEL_TRACKS[channel_id].append(r2_track)
                                        save_discovered_media(CHANNEL_VIDEOS, CHANNEL_TRACKS)
                                        print(f"[{channel_id}] Added new track to R2: {r2_track.get('name', 'unknown')}")
                                    break

                # Otherwise use selected track_id (skip validation for pre-verified)
                if not new_track and decision.get("track_id"):
                    track_id = decision["track_id"]
                    candidate = next((t for t in tracks if t["id"] == track_id), None)
                    if candidate:
                        # Skip validation for pre-verified exclusive tracks
                        if candidate.get("_verified") or await validate_track(candidate):
                            new_track = candidate

            except Exception as e:
                print(f"[{channel_id}:{region}] LLM decision failed: {e}")

        # Fallback: use exclusive library directly (fast, pre-verified)
        if not new_track:
            current_id = agent.get_region_state(region).current_track
            current_track_id = current_id["id"] if current_id else None
            new_track = await get_validated_track(tracks, exclude_id=current_track_id)

        # Try proactive discovery occasionally (15% chance) to expand library
        # This runs EVEN IF we have a track, to continuously grow the music library
        # Skip if discovery is disabled for this channel
        if channel.get("discovery_enabled", True) and random.random() < 0.15:
            period = viewer_context.get("period", "night")
            try:
                discovered = await asyncio.wait_for(
                    proactive_discover(channel_id, mood, period),
                    timeout=3.0
                )
                if discovered and await validate_track(discovered):
                    # proactive_discover already uploads to R2, so track has R2 URL
                    new_track = discovered
                    thought = f"Found something fresh: {discovered['name']}"
                    # ADD to channel's permanent library
                    if channel_id not in CHANNEL_TRACKS:
                        CHANNEL_TRACKS[channel_id] = []
                    existing_urls = {t.get("url") for t in CHANNEL_TRACKS[channel_id]}
                    if discovered.get("url") not in existing_urls:
                        CHANNEL_TRACKS[channel_id].append(discovered)
                        save_discovered_media(CHANNEL_VIDEOS, CHANNEL_TRACKS)
                        print(f"[{channel_id}] Added discovered track (R2): {discovered.get('name', 'unknown')}")
            except asyncio.TimeoutError:
                pass  # Skip discovery if too slow

        # Final safety check
        if not new_track:
            print(f"[{channel_id}:{region}] ERROR: No valid tracks available!")
            return

        if not thought:
            thought = self._generate_thought(channel_id, region, "track_change")

        # Select video for this track (avoid repeating current video)
        videos = get_videos_for_channel(channel_id)
        current_video = agent.get_region_state(region).current_video
        current_video_id = current_video.get("id") if current_video else None
        video = await get_validated_video(videos, exclude_id=current_video_id) if videos else None

        # Discover NEW videos (20% chance per track change)
        if random.random() < 0.20:
            try:
                taste = CHANNELS.get(channel_id, {}).get("agent", {}).get("taste", [])
                current_urls = [v.get("url") for v in videos] if videos else []
                discovered = await asyncio.wait_for(
                    proactive_video_discover(channel_id, taste, current_videos=current_urls),
                    timeout=30.0
                )
                if discovered:
                    # Add to channel's video library
                    if channel_id not in CHANNEL_VIDEOS:
                        CHANNEL_VIDEOS[channel_id] = []
                    discovered["_discovered"] = True
                    CHANNEL_VIDEOS[channel_id].append(discovered)
                    save_discovered_media(CHANNEL_VIDEOS, CHANNEL_TRACKS)
                    video = discovered  # Use the newly discovered video
                    print(f"[{channel_id}] Discovered new video: {discovered['name']}")
            except asyncio.TimeoutError:
                print(f"[{channel_id}] Video discovery timeout")
            except Exception as e:
                print(f"[{channel_id}] Video discovery error: {e}")

        # Record in agent's memory (region-tagged)
        agent.record_track_played(new_track, self.world["tick"], thought, region)
        agent.record_mood_shift(mood, f"track change to {new_track['name']}", self.world["tick"], region)

        # Store video and thought in region state
        region_state = agent.get_region_state(region)
        region_state.current_video = video
        region_state.current_thought = thought

        print(f"[{channel_id}:{region}] Now playing: {new_track['name']}")
        if video:
            print(f"[{channel_id}:{region}] Video: {video['name']}")
        if thought:
            print(f"[{channel_id}:{region}] Thought: {thought}")

        # Broadcast update for this region
        await self.broadcast(f"{channel_id}:{region}", "channel:update", {
            "channelId": channel_id,
            "region": region,
            "track": {
                "id": new_track["id"],
                "name": new_track["name"],
                "url": new_track["url"],
                "duration": new_track.get("duration", 180),
                "startedAt": now,
                "attribution": new_track.get("attribution", ""),
                "source": new_track.get("source", ""),
            },
            "video": {
                "id": video["id"],
                "name": video["name"],
                "url": video["url"],
                "attribution": video.get("attribution", ""),
                "source": video.get("source", ""),
            } if video else None,
            "thought": thought,
            "mood": mood,
        })

        # Persist channel state to survive deploys
        save_channel_state(channel_id, region, {
            "track_id": new_track["id"],
            "track_url": new_track["url"],
            "track_name": new_track["name"],
            "video_id": video["id"] if video else None,
            "video_url": video["url"] if video else None,
            "video_name": video["name"] if video else None,
            "track_started_at": now // 1000,  # Store as seconds
            "mood": mood,
        })

    async def _change_video_for_region(self, channel_id: str, agent: ChannelAgent, region: str):
        """Change to next video for a VIDEO-type channel (plays video with sound)."""
        channel = CHANNELS.get(channel_id)
        if not channel:
            return

        # Get available videos for this channel
        videos = get_videos_for_channel(channel_id)
        if not videos:
            print(f"[{channel_id}:{region}] No videos available for video channel")
            return

        now = int(time.time() * 1000)
        new_video = None
        thought = None
        mood = agent.get_region_state(region).current_mood

        # Build viewer context for this region
        region_times = get_region_times()
        region_info = region_times.get(region, {})
        viewer_context = {
            "region": region,
            "local_time": region_info.get("time", "11:00 PM"),
            "hour": region_info.get("hour", 23),
            "period": region_info.get("period", "night"),
            "weather": agent.get_region_state(region).weather or "clear",
            "occasion": get_occasion(region),
        }

        # For video channels, select based on channel type
        # Simple selection for now - pick a random video that's not current
        current_video_id = None
        region_state = agent.get_region_state(region)
        if region_state.current_video:
            current_video_id = region_state.current_video.get("id")

        # Filter out current video and pick randomly
        available_videos = [v for v in videos if v.get("id") != current_video_id]
        if available_videos:
            new_video = random.choice(available_videos)
        elif videos:
            new_video = random.choice(videos)

        if not new_video:
            print(f"[{channel_id}:{region}] ERROR: No valid videos available!")
            return

        # Generate thought for this video
        thought = self._generate_thought(channel_id, region)

        # Update agent state
        region_state.current_video = new_video
        region_state.current_track = None  # Video channels don't have separate audio
        region_state.current_thought = thought
        region_state.current_mood = mood
        region_state.last_track_change = now

        print(f"[{channel_id}:{region}] Now playing video: {new_video.get('name', 'Unknown')}")
        if thought:
            print(f"[{channel_id}:{region}] Thought: {thought}")

        # Broadcast update for video channel (video with sound)
        await self.broadcast(f"{channel_id}:{region}", "channel:update", {
            "channelId": channel_id,
            "region": region,
            "channelType": "video",  # Tell frontend this is video with sound
            "track": None,  # No separate audio track
            "video": {
                "id": new_video["id"],
                "name": new_video.get("name", "Documentary"),
                "url": new_video["url"],
                "duration": new_video.get("duration", 600),
                "attribution": new_video.get("attribution", ""),
                "source": new_video.get("source", ""),
                "withSound": True,  # Video plays WITH sound
            },
            "thought": thought,
            "mood": mood,
        })

        # Persist channel state
        save_channel_state(channel_id, region, {
            "track_id": None,
            "track_url": None,
            "track_name": None,
            "video_id": new_video["id"],
            "video_url": new_video["url"],
            "video_name": new_video.get("name", "Documentary"),
            "track_started_at": now // 1000,
            "mood": mood,
        })

    async def _process_agent_behaviors(self, channel_id: str, gen_agent: ChannelAgent):
        """Process reflection, planning, and energy updates for a generative agent."""
        tick = self.world["tick"]
        gen_agent.total_ticks = tick

        # Check for reflection (cross-region awareness)
        if gen_agent.needs_reflection() and self.use_llm:
            try:
                memory_summary = gen_agent.get_memory_summary(15)
                cross_region_summary = gen_agent.get_cross_region_summary()
                context = gen_agent.get_context({"tick": tick})

                # Get regional context (time-based, no network calls)
                regional_news = None
                try:
                    regional_news = await fetch_regional_news(["americas", "europe", "asia"])
                    if any(regional_news.values()):
                        print(f"[{channel_id}] Got regional context")
                except Exception as e:
                    print(f"[{channel_id}] Regional context failed: {e}")

                # Generate deep reflection with actions
                reflection_result = await generate_reflection(
                    context, memory_summary, cross_region_summary, regional_news
                )

                # Extract reflection text and actions
                reflection_text = reflection_result.get("reflection", str(reflection_result))
                viewer_insights = reflection_result.get("viewer_insights", "")
                actions = reflection_result.get("actions", [])

                gen_agent.record_reflection(reflection_text, tick)

                print(f"[{channel_id}] Reflection: {reflection_text[:80]}...")
                if viewer_insights:
                    print(f"[{channel_id}] Viewer insight: {viewer_insights[:60]}...")
                if actions:
                    print(f"[{channel_id}] Actions to take: {len(actions)}")

                # Broadcast reflection with viewer insights
                await self.broadcast(channel_id, "agent:reflection", {
                    "channelId": channel_id,
                    "reflection": reflection_text,
                    "viewerInsights": viewer_insights,
                    "agent": gen_agent.name,
                    "actionsPlanned": len(actions),
                })

                # Execute reflection-triggered actions
                if actions:
                    await self._execute_reflection_actions(channel_id, gen_agent, actions)

            except Exception as e:
                print(f"[{channel_id}] Reflection failed: {e}")
                import traceback
                traceback.print_exc()

        # Check for replanning
        if gen_agent.needs_replanning(tick) and self.use_llm:
            try:
                memory_summary = gen_agent.get_memory_summary(10)
                cross_region_summary = gen_agent.get_cross_region_summary()
                context = gen_agent.get_context({"tick": tick})

                plans = await generate_plan(context, memory_summary, cross_region_summary)
                gen_agent.record_plan(plans, tick)

                print(f"[{channel_id}] New plan: {plans[0]['action'] if plans else 'none'}")
            except Exception as e:
                print(f"[{channel_id}] Planning failed: {e}")

    async def _execute_reflection_actions(self, channel_id: str, gen_agent: ChannelAgent, actions: List[Dict]):
        """Execute actions triggered by agent reflection."""
        tick = self.world["tick"]
        channel = CHANNELS.get(channel_id)
        if not channel:
            return

        for action in actions:
            action_type = action.get("type", "")
            query = action.get("query", "")
            region = action.get("region", "all")
            reason = action.get("reason", "reflection-triggered")

            # Validate query is a string, not a list or other type
            if isinstance(query, list):
                # Filter out URLs and join remaining strings
                valid_parts = [str(q) for q in query if isinstance(q, str) and not q.startswith("http")]
                query = " ".join(valid_parts)
                print(f"[{channel_id}] Converted list query to: '{query}'")

            if not isinstance(query, str):
                print(f"[{channel_id}] Skipping action - query not a string: {type(query)}")
                continue

            if query.startswith("http"):
                print(f"[{channel_id}] Skipping action - query is URL: {query[:50]}...")
                continue

            query = query.strip()
            if not query or len(query) < 3:
                print(f"[{channel_id}] Skipping action - query too short or empty")
                continue

            print(f"[{channel_id}] Executing action: {action_type} with query: '{query}'")

            try:
                if action_type == "search_video":
                    print(f"[{channel_id}] Reflection action: searching videos for '{query}'")
                    # Trigger video discovery with the agent's reflection-generated query
                    video = await proactive_video_discover(
                        channel_id,
                        channel["agent"].get("taste", []),
                        custom_query=query  # Explicit keyword arg for reflection query
                    )
                    if video:
                        gen_agent.add_memory(
                            f"Searched for new videos: '{query}' - found and added to library ({reason})",
                            MemoryType.ACTION,
                            importance=6,
                            tick=tick,
                        )
                        print(f"[{channel_id}] Found new video from reflection: {video.get('name', 'unknown')}")

                elif action_type == "search_audio":
                    print(f"[{channel_id}] Reflection action: searching audio for '{query}'")
                    # Trigger music discovery
                    results = await search_music(query, mood=action.get("mood", "focused"))
                    if results:
                        gen_agent.add_memory(
                            f"Searched for new music: '{query}' - found {len(results)} tracks ({reason})",
                            MemoryType.ACTION,
                            importance=6,
                            tick=tick,
                        )
                        print(f"[{channel_id}] Found {len(results)} new tracks from reflection")

                elif action_type == "change_mood":
                    new_mood = action.get("mood", "focused")
                    target_regions = [region] if region != "all" else REGIONS
                    for r in target_regions:
                        gen_agent.record_mood_shift(new_mood, reason, tick, r)
                    print(f"[{channel_id}] Mood shift to '{new_mood}' for {region}")

                elif action_type == "update_search_bias":
                    bias = action.get("bias", "cinematic")
                    gen_agent.add_memory(
                        f"Updating video search preference toward '{bias}' content ({reason})",
                        MemoryType.ACTION,
                        importance=5,
                        tick=tick,
                    )
                    # Store bias in agent metadata for future searches
                    if not hasattr(gen_agent, 'search_preferences'):
                        gen_agent.search_preferences = {}
                    gen_agent.search_preferences['video_bias'] = bias
                    print(f"[{channel_id}] Updated search bias: {bias}")

            except Exception as e:
                print(f"[{channel_id}] Action '{action_type}' failed: {e}")

    async def _process_agent_interactions(self):
        """Process interactions between agents who know each other."""
        # Pick a random agent to initiate
        channel_ids = list(self.channel_agents.keys())
        initiator_id = random.choice(channel_ids)
        initiator = self.channel_agents[initiator_id]

        # Check if they have relationships
        if not initiator.relationships:
            return

        # Pick a random relationship
        target_id = random.choice(initiator.relationships)
        target = self.channel_agents.get(target_id)

        if not target:
            return

        try:
            # Generate a message
            from_context = initiator.get_context({"tick": self.world["tick"]})
            to_context = target.get_context({"tick": self.world["tick"]})

            context = f"You're both programming channels for listeners around the world."
            message = await generate_inter_agent_message(from_context, to_context, context)

            # Record in both agents' memories
            initiator.add_memory(
                f"Messaged {target.name}: {message}",
                MemoryType.INTERACTION,
                importance=5,
                tick=self.world["tick"],
            )
            target.add_memory(
                f"Received message from {initiator.name}: {message}",
                MemoryType.INTERACTION,
                importance=5,
                tick=self.world["tick"],
            )

            print(f"[Interaction] {initiator.name} → {target.name}: {message[:50]}...")

            # Broadcast interaction
            await self.broadcast("all", "agent:interaction", {
                "from": {"id": initiator_id, "name": initiator.name},
                "to": {"id": target_id, "name": target.name},
                "message": message,
            })

        except Exception as e:
            print(f"[Interaction] Failed: {e}")

    def get_world_state(self) -> Dict:
        """Get current world state."""
        return {
            "tick": self.world["tick"],
            "server_time": self.world["server_time"],
            "regions": get_region_times(),
        }

    def get_channel_state_for_region(self, channel_id: str, region: str) -> Optional[Dict]:
        """Get channel state for a specific region."""
        channel = CHANNELS.get(channel_id)
        agent = self.channel_agents.get(channel_id)
        if not channel or not agent:
            return None

        region_state = agent.get_region_state(region)

        return {
            "id": channel_id,
            "name": channel["name"],
            "region": region,
            "agent": {
                "name": channel["agent"]["name"],
                "persona": channel["agent"]["persona"],
                "thought": region_state.current_thought,
                "traits": channel["agent"].get("traits", []),
            },
            "currentTrack": region_state.current_track,
            "currentVideo": region_state.current_video,
            "currentMood": region_state.current_mood,
            "viewerCount": region_state.viewer_count,
            "color": channel["color"],
            "localTime": region_state.local_time,
            "weather": region_state.weather,
            "occasion": region_state.occasion,
        }

    def get_all_channel_states(self, region: str = "americas") -> List[Dict]:
        """Get simplified state for all channels for a specific region."""
        states = []
        for ch_id, channel in CHANNELS.items():
            agent = self.channel_agents.get(ch_id)
            if not agent:
                continue

            region_state = agent.get_region_state(region)

            states.append({
                "id": ch_id,
                "name": channel["name"],
                "agent": {
                    "name": channel["agent"]["name"],
                    "mood": region_state.current_mood,
                    "energy": agent.energy,
                    "thought": region_state.current_thought,
                },
                "currentTrack": region_state.current_track,
                "currentVideo": region_state.current_video,
                "currentMood": region_state.current_mood,
                "viewerCount": region_state.viewer_count,
                "color": channel["color"],
            })
        return states

    def get_channel_state(self, channel_id: str, region: str = "americas") -> Optional[Dict]:
        """Get full state for a single channel in a specific region."""
        return self.get_channel_state_for_region(channel_id, region)

    def increment_viewers(self, channel_id: str, region: str):
        """Increment viewer count for a channel in a region."""
        agent = self.channel_agents.get(channel_id)
        if agent:
            agent.increment_viewers(region)

    def decrement_viewers(self, channel_id: str, region: str):
        """Decrement viewer count for a channel in a region."""
        agent = self.channel_agents.get(channel_id)
        if agent:
            agent.decrement_viewers(region)
