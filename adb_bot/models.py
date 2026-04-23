from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple


ScreenName = Literal[
    "home_village",
    "builder_base",
    "attack_find_match",
    "battle",
    "battle_end",
    "upgrade_panel",
    "shop",
    "army_training",
    "popup_generic",
    "connection_lost",
    "loading",
    "unknown",
]

BotMode = Literal[
    "RECOVER",
    "IDLE_HOME",
    "COLLECT_RESOURCES",
    "UPGRADE_BUILDINGS",
    "UPGRADE_WALLS",
    "TRAIN_ARMY",
    "SEARCH_ATTACK",
    "EXECUTE_ATTACK",
    "POST_ATTACK",
    "HANDLE_POPUPS",
    "UNKNOWN",
]

AttackStrategy = Literal[
    "collector_snipe",
    "edge_funnel",
    "full_push",
    "townhall_snipe",
]


@dataclass
class ResourceState:
    gold: Optional[int] = None
    elixir: Optional[int] = None
    dark_elixir: Optional[int] = None
    gems: Optional[int] = None


@dataclass
class BuilderState:
    free: Optional[int] = None
    total: Optional[int] = None


@dataclass
class ArmyState:
    ready: bool = False
    capacity_used: Optional[int] = None
    heroes_ready: Optional[bool] = None
    spells_ready: Optional[bool] = None


@dataclass
class SelectedObjectState:
    object_type: Optional[str] = None
    level: Optional[int] = None
    upgrade_cost_gold: Optional[int] = None
    upgrade_cost_elixir: Optional[int] = None
    upgrade_available: bool = False
    insufficient_resources: bool = False


@dataclass
class VillageState:
    storages_possibly_full: bool = False
    collectors_ready: bool = False
    obstacles_present: bool = False


@dataclass
class BattleState:
    started: bool = False
    percent: Optional[int] = None
    stars: Optional[int] = None
    loot_visible: bool = False
    deployable_troops: List[str] = field(default_factory=list)


@dataclass
class UiState:
    popups_open: bool = False
    connection_lost: bool = False
    confirm_visible: bool = False
    back_visible: bool = False


@dataclass
class WorldState:
    timestamp: float
    screen: ScreenName
    resources: ResourceState = field(default_factory=ResourceState)
    builders: BuilderState = field(default_factory=BuilderState)
    army: ArmyState = field(default_factory=ArmyState)
    selected_object: SelectedObjectState = field(default_factory=SelectedObjectState)
    village: VillageState = field(default_factory=VillageState)
    battle: BattleState = field(default_factory=BattleState)
    ui: UiState = field(default_factory=UiState)
    available_actions: List[str] = field(default_factory=list)


@dataclass
class RuntimeFlags:
    same_screen_ticks: int = 0
    same_action_repeats: int = 0
    last_action_success: bool = True
    last_progress_timestamp: float = 0.0
    last_screen: ScreenName = "unknown"
    last_action_type: Optional[str] = None


@dataclass
class DetectionResult:
    name: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None
    text: Optional[str] = None


@dataclass
class BotAction:
    action_type: Literal["tap", "swipe", "long_press", "back", "wait", "retry", "noop"]
    reason: str
    x: Optional[int] = None
    y: Optional[int] = None
    x2: Optional[int] = None
    y2: Optional[int] = None
    duration_ms: Optional[int] = None
    wait_ms: Optional[int] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class TickContext:
    mode: BotMode
    world_state: WorldState
    runtime_flags: RuntimeFlags
