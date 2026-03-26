"""
Generative Agent Architecture for mood42
Based on Stanford's Generative Agents paper
Each channel programmer is a living agent with memory, reflection, and planning
Now with geo-awareness: one agent serves multiple regions with different content
"""

import time
import random
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum


# Define major timezone regions
REGIONS = ["americas", "europe", "asia", "oceania"]

# Map timezone offsets to regions (simplified)
TIMEZONE_TO_REGION = {
    # Americas (UTC-10 to UTC-3)
    **{i: "americas" for i in range(-10, -2)},
    # Europe/Africa (UTC-1 to UTC+3)
    **{i: "europe" for i in range(-1, 4)},
    # Asia (UTC+4 to UTC+9)
    **{i: "asia" for i in range(4, 10)},
    # Oceania (UTC+10 to UTC+12)
    **{i: "oceania" for i in range(10, 13)},
}


def get_region_from_timezone(tz_offset: int) -> str:
    """Get region from UTC offset in hours."""
    # Normalize to range -12 to +12
    tz_offset = max(-12, min(12, tz_offset))
    return TIMEZONE_TO_REGION.get(tz_offset, "europe")  # Default to europe


class MemoryType(Enum):
    OBSERVATION = "observation"
    ACTION = "action"
    REFLECTION = "reflection"
    PLAN = "plan"
    TRACK_PLAYED = "track_played"
    MOOD_SHIFT = "mood_shift"
    INTERACTION = "interaction"
    REGION_INSIGHT = "region_insight"  # New: insights about regional patterns


@dataclass
class Memory:
    """A single memory in the agent's stream."""
    text: str
    type: MemoryType
    importance: int  # 1-10
    tick: int
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    metadata: Dict = field(default_factory=dict)
    region: Optional[str] = None  # Which region this memory relates to

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "type": self.type.value,
            "importance": self.importance,
            "tick": self.tick,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "region": self.region,
        }


@dataclass
class RegionState:
    """State for a specific region."""
    region: str
    current_track: Optional[Dict] = None
    current_video: Optional[Dict] = None  # Current video playing
    current_mood: str = "focused"
    current_thought: Optional[str] = None  # Agent's current thought for this region
    viewer_count: int = 0
    track_history: List[Dict] = field(default_factory=list)
    last_track_change: int = 0

    # Region-specific context
    local_time: str = "11:00 PM"
    weather: str = "clear"
    occasion: Optional[str] = None  # Festival, holiday, etc.

    def to_dict(self) -> Dict:
        return {
            "region": self.region,
            "current_track": self.current_track,
            "current_video": self.current_video,
            "current_mood": self.current_mood,
            "current_thought": self.current_thought,
            "viewer_count": self.viewer_count,
            "local_time": self.local_time,
            "weather": self.weather,
            "occasion": self.occasion,
        }


@dataclass
class Plan:
    """A planned action."""
    time: str
    action: str
    duration: int = 30  # minutes, default 30
    region: Optional[str] = None  # Region-specific plan
    completed: bool = False

    def to_dict(self) -> Dict:
        return {
            "time": self.time,
            "action": self.action,
            "duration": self.duration,
            "region": self.region,
            "completed": self.completed,
        }


class ChannelAgent:
    """
    A generative agent that programs a mood42 channel.
    Has memory, can reflect, plan, and make decisions.
    Now geo-aware: manages different content for different regions.
    """

    # Constants
    MAX_MEMORIES = 200  # Increased for multi-region
    REFLECTION_THRESHOLD = 50
    PLAN_DURATION_TICKS = 12

    def __init__(
        self,
        channel_id: str,
        name: str,
        persona: str,
        traits: List[str],
        taste: List[str],
        relationships: List[str],
        initial_mood: str = "focused",
    ):
        self.channel_id = channel_id
        self.name = name
        self.persona = persona
        self.traits = traits
        self.taste = taste
        self.relationships = relationships

        # Global state
        self.energy = 0.8

        # Per-region state
        self.regions: Dict[str, RegionState] = {
            region: RegionState(region=region, current_mood=initial_mood)
            for region in REGIONS
        }

        # Memory stream (shared across regions, but tagged)
        self.memories: List[Memory] = []
        self.cumulative_importance = 0
        self.last_reflection_tick = 0

        # Planning (can be region-specific)
        self.plans: List[Plan] = []
        self.last_plan_tick = 0

        # Stats
        self.tracks_played = 0
        self.reflections_made = 0
        self.total_ticks = 0

        # Initialize with seed memories
        self._seed_memories()

    def _seed_memories(self):
        """Add initial memories that establish character."""
        seed_memories = [
            f"I am {self.name}, and I program the channel my way.",
            f"My taste runs toward {', '.join(self.taste[:3])}.",
            f"I serve listeners across the world - each region gets what fits their moment.",
            f"When it's morning in Tokyo, it might be evening in New York. I feel both.",
        ]
        for text in seed_memories:
            self.add_memory(text, MemoryType.OBSERVATION, importance=3, tick=0)

    def get_region_state(self, region: str) -> RegionState:
        """Get state for a specific region."""
        if region not in self.regions:
            self.regions[region] = RegionState(region=region)
        return self.regions[region]

    def set_region_state(self, region: str, track: Dict, video_url: str, mood: str, video_name: str, started_at: int):
        """Set state for a region - used for restoring state after deploy."""
        import time as time_module
        state = self.get_region_state(region)
        state.current_track = track
        state.current_video = {"url": video_url, "name": video_name, "id": f"restored_{region}"} if video_url else None
        state.current_mood = mood
        # Set to NOW so track doesn't immediately expire (pretend it just started)
        state.last_track_change = int(time_module.time() * 1000)
        print(f"[{self.channel_id}:{region}] Restored: {track.get('name', 'unknown')[:30]}")

    def add_memory(
        self,
        text: str,
        memory_type: MemoryType,
        importance: int = 5,
        tick: int = 0,
        metadata: Dict = None,
        region: str = None,
    ):
        """Add a memory to the stream, optionally tagged with region."""
        memory = Memory(
            text=text,
            type=memory_type,
            importance=importance,
            tick=tick,
            metadata=metadata or {},
            region=region,
        )
        self.memories.append(memory)
        self.cumulative_importance += importance

        # Trim old memories if needed
        if len(self.memories) > self.MAX_MEMORIES:
            self.memories = self.memories[-self.MAX_MEMORIES:]

    def needs_reflection(self) -> bool:
        """Check if agent should reflect based on accumulated importance."""
        return self.cumulative_importance >= self.REFLECTION_THRESHOLD

    def needs_replanning(self, current_tick: int) -> bool:
        """Check if agent needs to make a new plan."""
        if not self.plans:
            return True
        ticks_since_plan = current_tick - self.last_plan_tick
        return ticks_since_plan >= self.PLAN_DURATION_TICKS

    def get_recent_memories(
        self,
        count: int = 10,
        memory_type: MemoryType = None,
        region: str = None,
    ) -> List[Memory]:
        """Get recent memories, optionally filtered by type and/or region."""
        memories = self.memories
        if memory_type:
            memories = [m for m in memories if m.type == memory_type]
        if region:
            # Include both region-specific and global (None) memories
            memories = [m for m in memories if m.region is None or m.region == region]
        return memories[-count:]

    def recall(self, query: str, count: int = 5, region: str = None) -> List[Memory]:
        """
        Retrieve memories relevant to a query.
        Uses simple keyword matching + recency + importance scoring.
        """
        query_words = set(query.lower().split())

        # Filter by region if specified
        memories = self.memories
        if region:
            memories = [m for m in memories if m.region is None or m.region == region]

        def score_memory(memory: Memory) -> float:
            # Recency score (exponential decay)
            idx = memories.index(memory) if memory in memories else 0
            age = len(memories) - idx
            recency = 0.99 ** age

            # Importance score (normalized)
            importance = memory.importance / 10.0

            # Relevance score (keyword matching)
            memory_words = set(memory.text.lower().split())
            overlap = len(query_words & memory_words)
            relevance = overlap / max(len(query_words), 1)

            # Boost region-specific memories
            region_boost = 1.2 if memory.region == region else 1.0

            return ((recency + importance + relevance) / 3) * region_boost

        scored = [(m, score_memory(m)) for m in memories]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [m for m, _ in scored[:count]]

    def record_track_played(
        self,
        track: Dict,
        tick: int,
        thought: str = None,
        region: str = None,
    ):
        """Record that a track was played for a specific region."""
        self.tracks_played += 1

        # Update region state
        if region:
            state = self.get_region_state(region)
            state.current_track = track
            state.last_track_change = int(time.time() * 1000)
            state.track_history.append({
                "track_id": track["id"],
                "played_at": state.last_track_change,
            })
            # Keep only last 20 per region
            state.track_history = state.track_history[-20:]

        region_text = f" for {region}" if region else ""
        text = f"Played '{track['name']}'{region_text}"
        if thought:
            text += f" — {thought}"

        self.add_memory(
            text=text,
            memory_type=MemoryType.TRACK_PLAYED,
            importance=4,
            tick=tick,
            metadata={"track_id": track["id"], "region": region},
            region=region,
        )

    def record_mood_shift(self, new_mood: str, reason: str, tick: int, region: str = None):
        """Record a mood change for a specific region."""
        if region:
            state = self.get_region_state(region)
            old_mood = state.current_mood
            state.current_mood = new_mood
        else:
            old_mood = "unknown"

        region_text = f" in {region}" if region else ""
        self.add_memory(
            text=f"Mood shifted{region_text} from {old_mood} to {new_mood}: {reason}",
            memory_type=MemoryType.MOOD_SHIFT,
            importance=6,
            tick=tick,
            region=region,
        )

    def record_region_insight(self, insight: str, regions: List[str], tick: int):
        """Record an insight about patterns across regions."""
        self.add_memory(
            text=f"Cross-region insight ({', '.join(regions)}): {insight}",
            memory_type=MemoryType.REGION_INSIGHT,
            importance=7,
            tick=tick,
            metadata={"regions": regions},
        )

    def record_reflection(self, reflection: str, tick: int):
        """Record a reflection and reset importance counter."""
        self.add_memory(
            text=f"Reflection: {reflection}",
            memory_type=MemoryType.REFLECTION,
            importance=8,
            tick=tick,
        )
        self.cumulative_importance = 0
        self.last_reflection_tick = tick
        self.reflections_made += 1

    def record_plan(self, plans: List[Dict], tick: int):
        """Record new plans."""
        self.plans = [Plan(**p) for p in plans]
        self.last_plan_tick = tick

        plan_summary = ", ".join([p["action"] for p in plans[:3]])
        self.add_memory(
            text=f"Made plans: {plan_summary}",
            memory_type=MemoryType.PLAN,
            importance=5,
            tick=tick,
        )

    def get_current_plan(self, region: str = None) -> Optional[Plan]:
        """Get the current uncompleted plan, optionally for a specific region."""
        for plan in self.plans:
            if not plan.completed:
                if region is None or plan.region is None or plan.region == region:
                    return plan
        return None

    def complete_current_plan(self, region: str = None):
        """Mark current plan as completed."""
        plan = self.get_current_plan(region)
        if plan:
            plan.completed = True

    def update_region_context(
        self,
        region: str,
        local_time: str = None,
        weather: str = None,
        occasion: str = None,
    ):
        """Update context for a specific region."""
        state = self.get_region_state(region)
        if local_time:
            state.local_time = local_time
        if weather:
            state.weather = weather
        if occasion is not None:  # Allow clearing with empty string
            state.occasion = occasion or None

    def increment_viewers(self, region: str):
        """Increment viewer count for a region."""
        self.get_region_state(region).viewer_count += 1

    def decrement_viewers(self, region: str):
        """Decrement viewer count for a region."""
        state = self.get_region_state(region)
        state.viewer_count = max(0, state.viewer_count - 1)

    def get_context(self, world_state: Dict, region: str = None) -> Dict:
        """Get current context for LLM prompts, optionally region-specific."""
        # Get region-specific recent tracks
        recent_tracks = [
            m.metadata.get("track_id")
            for m in self.get_recent_memories(5, MemoryType.TRACK_PLAYED, region)
            if m.metadata.get("track_id")
        ]

        # Get region state
        region_state = self.get_region_state(region) if region else None

        # Build cross-region summary
        all_regions_summary = {
            r: {
                "track": s.current_track["name"] if s.current_track else None,
                "mood": s.current_mood,
                "viewers": s.viewer_count,
                "time": s.local_time,
            }
            for r, s in self.regions.items()
        }

        return {
            "name": self.name,
            "channel_id": self.channel_id,
            "persona": self.persona,
            "traits": self.traits,
            "taste": self.taste,
            "energy": self.energy,
            # Region-specific
            "region": region,
            "local_time": region_state.local_time if region_state else "11:00 PM",
            "local_weather": region_state.weather if region_state else "clear",
            "occasion": region_state.occasion if region_state else None,
            "region_mood": region_state.current_mood if region_state else "focused",
            "region_viewers": region_state.viewer_count if region_state else 0,
            # Cross-region awareness
            "all_regions": all_regions_summary,
            "recent_tracks": recent_tracks,
            "tracks_played_total": self.tracks_played,
            "current_plan": self.get_current_plan(region).to_dict() if self.get_current_plan(region) else None,
        }

    def get_memory_summary(self, count: int = 10, region: str = None) -> str:
        """Get a text summary of recent memories."""
        memories = self.get_recent_memories(count, region=region)
        return "\n".join([f"- {m.text}" for m in memories])

    def get_cross_region_summary(self) -> str:
        """Get a summary of what's happening across all regions."""
        lines = []
        for region, state in self.regions.items():
            track_name = state.current_track["name"] if state.current_track else "none"
            lines.append(
                f"- {region.upper()}: {state.local_time}, {state.current_mood} mood, "
                f"playing '{track_name}', {state.viewer_count} viewers"
            )
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Serialize agent state."""
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "energy": self.energy,
            "tracks_played": self.tracks_played,
            "reflections_made": self.reflections_made,
            "memory_count": len(self.memories),
            "cumulative_importance": self.cumulative_importance,
            "regions": {r: s.to_dict() for r, s in self.regions.items()},
            "current_plan": self.get_current_plan().to_dict() if self.get_current_plan() else None,
        }


def create_channel_agents(channels: Dict) -> Dict[str, ChannelAgent]:
    """Create agents for all channels."""
    agents = {}

    for ch_id, channel in channels.items():
        agent_data = channel.get("agent", {})
        agents[ch_id] = ChannelAgent(
            channel_id=ch_id,
            name=agent_data.get("name", "Unknown"),
            persona=agent_data.get("persona", ""),
            traits=agent_data.get("traits", []),
            taste=agent_data.get("taste", []),
            relationships=agent_data.get("relationships", []),
            initial_mood=channel.get("currentMood", "focused"),
        )

    return agents
