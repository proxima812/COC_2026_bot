from __future__ import annotations

from dataclasses import dataclass
import random

from . import config


@dataclass
class Bot2ADBState:
    search_requested: bool = False
    battle_active: bool = False
    cooldown_until: float = 0.0
    next_2_9_at: float = 0.0
    next_1_at: float = 0.0
    next_2_9_deploy_at: float = 0.0
    completed_attacks: int = 0
    pending_base_macro: bool = False

    def mark_search(self, now_ts: float):
        self.search_requested = True
        self.cooldown_until = now_ts + config.BOT2_ADB_SEARCH_RETRY_SECONDS

    def start_battle(self, now_ts: float):
        self.search_requested = True
        self.battle_active = True
        self.cooldown_until = now_ts + config.BOT2_ADB_ATTACK_COOLDOWN_SECONDS
        self.next_2_9_at = now_ts + random.uniform(
            config.BOT2_ADB_SWEEP_2_9_MIN_SECONDS,
            config.BOT2_ADB_SWEEP_2_9_MAX_SECONDS,
        )
        self.next_1_at = now_ts + random.uniform(
            config.BOT2_ADB_PRESS_1_MIN_SECONDS,
            config.BOT2_ADB_PRESS_1_MAX_SECONDS,
        )
        self.next_2_9_deploy_at = now_ts + random.uniform(
            config.BOT2_ADB_SWEEP_2_9_DEPLOY_MIN_SECONDS,
            config.BOT2_ADB_SWEEP_2_9_DEPLOY_MAX_SECONDS,
        )

    def reschedule_2_9(self, now_ts: float):
        self.next_2_9_at = now_ts + random.uniform(
            config.BOT2_ADB_SWEEP_2_9_MIN_SECONDS,
            config.BOT2_ADB_SWEEP_2_9_MAX_SECONDS,
        )

    def reschedule_1(self, now_ts: float):
        self.next_1_at = now_ts + random.uniform(
            config.BOT2_ADB_PRESS_1_MIN_SECONDS,
            config.BOT2_ADB_PRESS_1_MAX_SECONDS,
        )

    def reschedule_2_9_deploy(self, now_ts: float):
        self.next_2_9_deploy_at = now_ts + random.uniform(
            config.BOT2_ADB_SWEEP_2_9_DEPLOY_MIN_SECONDS,
            config.BOT2_ADB_SWEEP_2_9_DEPLOY_MAX_SECONDS,
        )

    def finish_attack(self, now_ts: float, cooldown: float):
        self.search_requested = False
        self.battle_active = False
        self.next_2_9_at = 0.0
        self.next_1_at = 0.0
        self.next_2_9_deploy_at = 0.0
        self.cooldown_until = now_ts + max(0.0, cooldown)
        self.completed_attacks += 1
        if self.completed_attacks % max(1, int(config.BOT2_ADB_BASE_MACRO_EVERY_ATTACKS)) == 0:
            self.pending_base_macro = True

    def clear_pending_base_macro(self):
        self.pending_base_macro = False
