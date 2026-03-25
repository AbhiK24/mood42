"""
Generative Agent Architecture for mood42
Based on Stanford's Generative Agents paper
Each channel programmer is a living agent with memory, reflection, and planning
"""

import time
import random
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class MemoryType(Enum):
    OBSERVATION = "observation"
    ACTION = "action"
    REFLECTION = "reflection"
    PLAN = "plan"
    TRACK_PLAYED = "track_played"
    MOOD_SHIFT = "mood_shift"
    INTERACTION = "interaction"


@dataclass
class Memory:
    """A single memory in the agent's stream."""
    text: str
    type: MemoryType
    importance: int  # 1-10
    tick: int
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "type": self.type.value,
            "importance": self.importance,
            "tick": self.tick,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class Plan:
    """A planned action."""
    time: str
    action: str
    duration: int  # minutes
    completed: bool = False

    def to_dict(self) -> Dict:
        return {
            "time": self.time,
            "action": self.action,
            "duration": self.duration,
            "completed": self.completed,
        }


class ChannelAgent:
    """
    A generative agent that programs a mood42 channel.
    Has memory, can reflect, plan, and make decisions.
    """

    # Constants
    MAX_MEMORIES = 100
    REFLECTION_THRESHOLD = 50  # Cumulative importance before reflection
    PLAN_DURATION_TICKS = 12  # Re-plan every 12 ticks (~1 hour sim time)

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
        self.relationships = relationships  # Other channel IDs this agent knows

        # State
        self.mood = initial_mood
        self.energy = 0.8  # 0-1
        self.current_track = None
        self.current_visual = None

        # Memory stream
        self.memories: List[Memory] = []
        self.cumulative_importance = 0
        self.last_reflection_tick = 0

        # Planning
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
            f"The late hours are when I do my best work.",
        ]
        for text in seed_memories:
            self.add_memory(text, MemoryType.OBSERVATION, importance=3, tick=0)

    def add_memory(
        self,
        text: str,
        memory_type: MemoryType,
        importance: int = 5,
        tick: int = 0,
        metadata: Dict = None,
    ):
        """Add a memory to the stream."""
        memory = Memory(
            text=text,
            type=memory_type,
            importance=importance,
            tick=tick,
            metadata=metadata or {},
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

    def get_recent_memories(self, count: int = 10, memory_type: MemoryType = None) -> List[Memory]:
        """Get recent memories, optionally filtered by type."""
        memories = self.memories
        if memory_type:
            memories = [m for m in memories if m.type == memory_type]
        return memories[-count:]

    def recall(self, query: str, count: int = 5) -> List[Memory]:
        """
        Retrieve memories relevant to a query.
        Uses simple keyword matching + recency + importance scoring.
        """
        query_words = set(query.lower().split())

        def score_memory(memory: Memory) -> float:
            # Recency score (exponential decay)
            age = len(self.memories) - self.memories.index(memory)
            recency = 0.99 ** age

            # Importance score (normalized)
            importance = memory.importance / 10.0

            # Relevance score (keyword matching)
            memory_words = set(memory.text.lower().split())
            overlap = len(query_words & memory_words)
            relevance = overlap / max(len(query_words), 1)

            return (recency + importance + relevance) / 3

        scored = [(m, score_memory(m)) for m in self.memories]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [m for m, _ in scored[:count]]

    def record_track_played(self, track: Dict, tick: int, thought: str = None):
        """Record that a track was played."""
        self.current_track = track
        self.tracks_played += 1

        text = f"Played '{track['name']}'"
        if thought:
            text += f" — {thought}"

        self.add_memory(
            text=text,
            memory_type=MemoryType.TRACK_PLAYED,
            importance=4,
            tick=tick,
            metadata={"track_id": track["id"]},
        )

    def record_mood_shift(self, new_mood: str, reason: str, tick: int):
        """Record a mood change."""
        old_mood = self.mood
        self.mood = new_mood

        self.add_memory(
            text=f"Mood shifted from {old_mood} to {new_mood}: {reason}",
            memory_type=MemoryType.MOOD_SHIFT,
            importance=6,
            tick=tick,
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

        plan_summary = ", ".join([p.action for p in self.plans[:3]])
        self.add_memory(
            text=f"Made plans: {plan_summary}",
            memory_type=MemoryType.PLAN,
            importance=5,
            tick=tick,
        )

    def get_current_plan(self) -> Optional[Plan]:
        """Get the current uncompleted plan."""
        for plan in self.plans:
            if not plan.completed:
                return plan
        return None

    def complete_current_plan(self):
        """Mark current plan as completed."""
        plan = self.get_current_plan()
        if plan:
            plan.completed = True

    def update_energy(self, time_of_day: int):
        """Update energy based on time of day and agent traits."""
        hour = (time_of_day // 60) % 24

        # Night owls get energy at night
        if "night owl" in " ".join(self.traits).lower():
            if 22 <= hour or hour < 6:
                self.energy = min(1.0, self.energy + 0.05)
            else:
                self.energy = max(0.3, self.energy - 0.02)
        # Early birds get energy in morning
        elif "early" in " ".join(self.traits).lower():
            if 5 <= hour < 12:
                self.energy = min(1.0, self.energy + 0.05)
            else:
                self.energy = max(0.3, self.energy - 0.02)
        else:
            # Normal energy curve
            if 9 <= hour < 17:
                self.energy = min(1.0, self.energy + 0.02)
            elif 23 <= hour or hour < 5:
                self.energy = max(0.3, self.energy - 0.03)

    def get_context(self, world_state: Dict) -> Dict:
        """Get current context for LLM prompts."""
        recent_tracks = [
            m.metadata.get("track_id")
            for m in self.get_recent_memories(5, MemoryType.TRACK_PLAYED)
            if m.metadata.get("track_id")
        ]

        return {
            "name": self.name,
            "channel_id": self.channel_id,
            "persona": self.persona,
            "traits": self.traits,
            "taste": self.taste,
            "mood": self.mood,
            "energy": self.energy,
            "time": world_state.get("timeString", "11:00 PM"),
            "weather": world_state.get("weather", {}),
            "recent_tracks": recent_tracks,
            "tracks_played_total": self.tracks_played,
            "current_plan": self.get_current_plan().to_dict() if self.get_current_plan() else None,
        }

    def get_memory_summary(self, count: int = 10) -> str:
        """Get a text summary of recent memories."""
        memories = self.get_recent_memories(count)
        return "\n".join([f"- {m.text}" for m in memories])

    def to_dict(self) -> Dict:
        """Serialize agent state."""
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "mood": self.mood,
            "energy": self.energy,
            "tracks_played": self.tracks_played,
            "reflections_made": self.reflections_made,
            "memory_count": len(self.memories),
            "cumulative_importance": self.cumulative_importance,
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
