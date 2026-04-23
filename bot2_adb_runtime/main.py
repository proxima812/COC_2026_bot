from __future__ import annotations

from . import config
from .actions import (
    close_not_loot_ui,
    deploy_attack,
    handle_star_bonus,
    now,
    press_1,
    press_2_to_9,
    press_2_to_9_then_deploy,
    return_home,
    run_base_macro,
    run_search,
    sleep_for,
    sleep_loop,
)
from .adb import ADBClient
from .detector import TemplateDetector
from .logger import log
from .state import Bot2ADBState


def main():
    detector = TemplateDetector()
    missing_templates = detector.missing_required_templates()
    if missing_templates:
        log(f'missing image templates in {config.BOT2_ADB_IMAGES_DIR}: {", ".join(missing_templates)}')
        log('add files and restart.')
        return

    missing_fields = config.missing_required_fields()
    if missing_fields:
        log('fill these config fields before run 2-adb:')
        for field_name in missing_fields:
            log(f'  - {field_name}')
        return

    adb = ADBClient()
    try:
        adb.prepare()
    except Exception as exc:
        log(f'adb prepare failed: {exc}')
        return

    if not adb.is_ready():
        log('adb device not ready. Start emulator, enable adb, then retry.')
        return

    state = Bot2ADBState()
    last_debug_log_at = 0.0
    log(f'starting in {config.BOT2_ADB_START_DELAY_SECONDS:.0f} seconds')
    sleep_for(adb, config.BOT2_ADB_START_DELAY_SECONDS)
    log(
        'started; '
        f'adb screen size={adb.screen_size()} '
        f'home_conf={config.BOT2_ADB_HOME_CONFIDENCE:.2f} '
        f'attack_conf={config.BOT2_ADB_ATTACK_READY_CONFIDENCE:.2f}'
    )

    while True:
        now_ts = now()
        if now_ts < state.cooldown_until:
            sleep_loop(adb)
            continue

        try:
            frame_rgb = adb.capture_frame_rgb()
        except Exception as exc:
            log(f'adb screencap failed: {exc}')
            sleep_loop(adb)
            continue

        star_bonus_match = detector.find_any(
            frame_rgb,
            (config.BOT2_ADB_STAR_BONUS_IMAGE,),
            region=config.BOT2_ADB_STAR_BONUS_REGION,
            confidence=config.BOT2_ADB_STAR_BONUS_CONFIDENCE,
        )
        if star_bonus_match is not None:
            log(f'detected {star_bonus_match.name} score={star_bonus_match.score:.3f}')
            handle_star_bonus(adb)
            state.finish_attack(now(), config.BOT2_ADB_AFTER_STAR_BONUS_COOLDOWN)
            sleep_loop(adb)
            continue

        return_home_match = detector.find_any(
            frame_rgb,
            (config.BOT2_ADB_RETURN_HOME_IMAGE,),
            region=config.BOT2_ADB_RETURN_HOME_REGION,
            confidence=config.BOT2_ADB_RETURN_HOME_CONFIDENCE,
        )
        if return_home_match is not None:
            log(f'detected {return_home_match.name} score={return_home_match.score:.3f}')
            return_home(adb)
            state.finish_attack(now(), config.BOT2_ADB_AFTER_RETURN_HOME_COOLDOWN)
            sleep_loop(adb)
            continue

        if state.completed_attacks > 0 and (
            state.completed_attacks % max(1, int(config.BOT2_ADB_NOT_LOOT_CHECK_EVERY_ATTACKS)) == 0
        ):
            not_loot_match = detector.find_any(
                frame_rgb,
                config.BOT2_ADB_NOT_LOOT_IMAGES,
                region=config.BOT2_ADB_NOT_LOOT_REGION,
                confidence=config.BOT2_ADB_NOT_LOOT_CONFIDENCE,
            )
            if not_loot_match is not None:
                log(f'detected {not_loot_match.name} score={not_loot_match.score:.3f}')
                close_not_loot_ui(adb)
                state.search_requested = False
                state.battle_active = False
                state.cooldown_until = now() + config.BOT2_ADB_ATTACK_COOLDOWN_SECONDS
                sleep_loop(adb)
                continue

        home_match = detector.find_any(
            frame_rgb,
            config.BOT2_ADB_HOME_IMAGES,
            region=config.BOT2_ADB_HOME_REGION,
            confidence=config.BOT2_ADB_HOME_CONFIDENCE,
        )

        if state.pending_base_macro and home_match is not None:
            log(f'detected {home_match.name} score={home_match.score:.3f} -> run base macro')
            run_base_macro(adb)
            state.clear_pending_base_macro()
            sleep_loop(adb)
            continue

        if not state.search_requested and home_match is not None:
            log(f'detected {home_match.name} score={home_match.score:.3f} -> run search')
            run_search(adb)
            state.mark_search(now())
            sleep_loop(adb)
            continue

        if state.search_requested and home_match is not None:
            log(f'detected {home_match.name} score={home_match.score:.3f} -> retry search')
            run_search(adb)
            state.mark_search(now())
            sleep_loop(adb)
            continue

        attack_ready_match = detector.find_any(
            frame_rgb,
            config.BOT2_ADB_ATTACK_READY_IMAGES,
            region=config.BOT2_ADB_ATTACK_READY_REGION,
            confidence=config.BOT2_ADB_ATTACK_READY_CONFIDENCE,
        )
        if state.search_requested and attack_ready_match is not None:
            log(f'detected {attack_ready_match.name} score={attack_ready_match.score:.3f} -> deploy attack')
            deploy_attack(adb)
            state.start_battle(now())
            sleep_loop(adb)
            continue

        if state.battle_active:
            now_ts = now()
            if now_ts >= state.next_2_9_at:
                press_2_to_9(adb)
                state.reschedule_2_9(now_ts)
            if now_ts >= state.next_1_at:
                press_1(adb)
                state.reschedule_1(now_ts)
            if now_ts >= state.next_2_9_deploy_at:
                press_2_to_9_then_deploy(adb)
                state.reschedule_2_9_deploy(now_ts)

        now_ts = now()
        if now_ts - last_debug_log_at >= max(1.0, float(config.BOT2_ADB_DEBUG_LOG_INTERVAL_SECONDS)):
            home_best = detector.best_any(
                frame_rgb,
                config.BOT2_ADB_HOME_IMAGES,
                region=config.BOT2_ADB_HOME_REGION,
            )
            attack_best = detector.best_any(
                frame_rgb,
                config.BOT2_ADB_ATTACK_READY_IMAGES,
                region=config.BOT2_ADB_ATTACK_READY_REGION,
            )
            return_best = detector.best_any(
                frame_rgb,
                (config.BOT2_ADB_RETURN_HOME_IMAGE,),
                region=config.BOT2_ADB_RETURN_HOME_REGION,
            )
            star_best = detector.best_any(
                frame_rgb,
                (config.BOT2_ADB_STAR_BONUS_IMAGE,),
                region=config.BOT2_ADB_STAR_BONUS_REGION,
            )

            def fmt(match):
                if match is None:
                    return 'n/a'
                return f'{match.name}:{match.score:.3f}@x{match.scale:.2f}'

            log(
                'idle-debug '
                f'home={fmt(home_best)} '
                f'attack={fmt(attack_best)} '
                f'return={fmt(return_best)} '
                f'star={fmt(star_best)} '
                f'search_requested={state.search_requested} '
                f'battle_active={state.battle_active}'
            )
            last_debug_log_at = now_ts

        sleep_loop(adb)
