import pyautogui

from . import config
from .actions import (
    close_not_loot_ui,
    deploy_attack,
    handle_star_bonus,
    now,
    press_1,
    press_2_to_9,
    press_2_to_9_then_g,
    return_home,
    run_base_macro,
    run_search,
    sleep_for,
    sleep_loop,
)
from .detector import has_any, has_image, missing_required_templates
from .logger import log
from .state import Bot2State


def main():
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.04

    missing = missing_required_templates()
    if missing:
        log(f'missing image templates in {config.BOT2_IMAGES_DIR}: {", ".join(missing)}')
        log('add files and restart.')
        return

    state = Bot2State()
    log(f'starting in {config.BOT2_START_DELAY_SECONDS:.0f} seconds')
    sleep_for(config.BOT2_START_DELAY_SECONDS)
    log('started')

    while True:
        now_ts = now()
        if now_ts < state.cooldown_until:
            sleep_loop()
            continue

        if has_image(config.BOT2_STAR_BONUS_IMAGE):
            handle_star_bonus()
            state.finish_attack(now(), config.BOT2_AFTER_DASH_COOLDOWN)
            sleep_loop()
            continue

        if has_image(config.BOT2_RETURN_HOME_IMAGE):
            return_home()
            state.finish_attack(now(), config.BOT2_AFTER_H_COOLDOWN)
            sleep_loop()
            continue

        if (
            state.completed_attacks > 0
            and state.completed_attacks % max(1, int(config.BOT2_NOT_LOOT_CHECK_EVERY_ATTACKS)) == 0
            and has_any(config.BOT2_NOT_LOOT_IMAGES)
        ):
            close_not_loot_ui()
            state.search_requested = False
            state.battle_active = False
            state.cooldown_until = now() + config.BOT2_ATTACK_COOLDOWN_SECONDS
            sleep_loop()
            continue

        if state.pending_base_macro and has_any(config.BOT2_HOME_IMAGES):
            run_base_macro()
            state.clear_pending_base_macro()
            sleep_loop()
            continue

        if not state.search_requested and has_any(config.BOT2_HOME_IMAGES):
            run_search()
            state.mark_search(now())
            sleep_loop()
            continue

        if state.search_requested and has_any(config.BOT2_HOME_IMAGES):
            log('still on home screen, retry search sequence')
            run_search()
            state.mark_search(now())
            sleep_loop()
            continue

        if state.search_requested and has_any(config.BOT2_ATTACK_READY_IMAGES):
            deploy_attack()
            state.start_battle(now())
            sleep_loop()
            continue

        if state.battle_active:
            now_ts = now()
            if now_ts >= state.next_2_9_at:
                press_2_to_9()
                state.reschedule_2_9(now_ts)
            if now_ts >= state.next_1_at:
                press_1()
                state.reschedule_1(now_ts)
            if now_ts >= state.next_2_9_g_at:
                press_2_to_9_then_g()
                state.reschedule_2_9_g(now_ts)

        sleep_loop()
