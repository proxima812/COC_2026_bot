from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AdbConfig:
    host: str = "127.0.0.1"
    port: int = 5555
    screenshot_timeout_seconds: float = 4.0
    command_timeout_seconds: float = 5.0
    loop_interval_seconds: float = 1.0
    action_retry_limit: int = 3
    same_screen_threshold: int = 10
    same_action_threshold: int = 3
    no_progress_timeout_seconds: float = 60.0
    loading_timeout_seconds: float = 20.0
    home_confidence: float = 0.88
    button_confidence: float = 0.88
    ocr_retry_frames: int = 2
    storage_near_full_ratio: float = 0.92
    unknown_screen_screenshot_limit: int = 25
    upgrade_priority: list[str] = field(
        default_factory=lambda: [
            "laboratory",
            "army_camp",
            "clan_castle",
            "spell_factory",
            "barracks",
            "hero",
            "air_defense",
            "inferno",
            "x_bow",
            "wizard_tower",
            "archer_tower",
            "cannon",
            "mortar",
            "wall",
        ]
    )
