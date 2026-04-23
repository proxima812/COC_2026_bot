
import argparse
import os
import time

import pyautogui

import attack
import config as cfg
import gold_filter
import input_profile
import live_config as lcfg
import recovery_watchdog
import runtime_state
import storage_monitor
import telegram_reporter
from bot_runtime import screen_state
from recovery_watchdog import RecoveryIssue


def handle_okay_after_battle():
    if not bool(getattr(cfg, 'ENABLE_OKAY_AFTER_BATTLE', True)):
        return False

    image_paths = screen_state.resolve_image_paths(
        'OKAY_AFTER_BATTLE_IMAGE_PATHS',
        'OKAY_AFTER_BATTLE_IMAGE_PATH',
        'images/okay.png',
    )
    existing_paths = [image_path for image_path in image_paths if image_path and os.path.exists(image_path)]
    if not existing_paths:
        return False

    region = getattr(cfg, 'OKAY_AFTER_BATTLE_SEARCH_REGION', None)
    confidence = lcfg.get_float('IMAGE_MATCH_CONFIDENCE', getattr(cfg, 'IMAGE_MATCH_CONFIDENCE', 0.88))
    deadline = time.time() + max(0.0, float(getattr(cfg, 'OKAY_AFTER_BATTLE_CHECK_SECONDS', 4.0)))
    poll_interval = max(0.1, float(getattr(cfg, 'OKAY_AFTER_BATTLE_POLL_INTERVAL_SECONDS', 0.4)))
    okay_key = lcfg.get_str('OKAY_AFTER_BATTLE_KEY', '=').strip() or '='

    while time.time() <= deadline:
        for image_path in existing_paths:
            match = screen_state.locate_image(image_path, region=region, confidence=confidence)
            if match is not None:
                telegram_reporter.append_console_log(f'Okay screen detected -> press {okay_key}.')
                pyautogui.press(okay_key)
                return True
        pyautogui.sleep(poll_interval)
    return False


def check_storages_full():
    check_storages_full.counter += 1
    if check_storages_full.counter >= cfg.STORAGE_CHECK_LIMIT:
        return True
    return False

check_storages_full.counter = 0

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.04
input_profile.apply()

def main():
    input_profile.refresh_if_needed()
    watchdog = recovery_watchdog.RecoveryWatchdog(
        bot_entry_path=__file__,
        locate_image_fn=screen_state.locate_image,
    )
    check_storages_full.counter = 0
    try:
        runtime_state.reset_session_state()
    except OSError as exc:
        print(f"Runtime state reset failed: {exc}")
    telegram_reporter.append_console_log('Bot loop started.')

    start_delay = lcfg.get_float('START_DELAY_SECONDS', cfg.START_DELAY_SECONDS)
    print(f"Starting in {start_delay} seconds. Switch to Bluestacks window.")
    pyautogui.sleep(start_delay)
    while True:
        try:
            input_profile.refresh_if_needed()
            watchdog.start_loop()
            watchdog.heartbeat('loop_start')

            issue = watchdog.detect_issue()
            if issue is not None:
                if watchdog.handle_issue(issue):
                    pyautogui.sleep(1)
                    continue

            if runtime_state.consume_timing_reload_request():
                print("Timing update applied: starting a fresh cycle.")
                watchdog.heartbeat('timing_reload')

            watchdog.heartbeat('wait_search_button')
            if not screen_state.wait_for_search_button_screen():
                wait_failure = screen_state.consume_last_wait_failure()
                if wait_failure and wait_failure.get('code') in ('guard_retry_limit', 'guard_timeout'):
                    issue = RecoveryIssue(wait_failure.get('code', 'guard_retry_limit'), wait_failure.get('details', 'search button not found'))
                    if watchdog.handle_issue(issue):
                        pyautogui.sleep(1)
                        continue
                telegram_reporter.append_console_log('Home guard not ready, retry.')
                pyautogui.sleep(1)
                continue

            watchdog.heartbeat('home_ready')
            telegram_reporter.append_console_log('Home screen detected.')
            watchdog.heartbeat('search_attack')
            telegram_reporter.append_console_log('Starting search attack.')
            attack.search_attack()
            watchdog.heartbeat('wait_army_ready')
            if not screen_state.wait_for_army_ready_screen():
                wait_failure = screen_state.consume_last_wait_failure()
                if wait_failure and wait_failure.get('code') in ('guard_retry_limit', 'guard_timeout'):
                    issue = RecoveryIssue(wait_failure.get('code', 'guard_retry_limit'), wait_failure.get('details', 'army ready not found'))
                    if watchdog.handle_issue(issue):
                        pyautogui.sleep(1)
                        continue
                telegram_reporter.append_console_log('Battle guard not ready, retry.')
                pyautogui.sleep(1)
                continue
            telegram_reporter.append_console_log('Battle screen detected.')
            watchdog.heartbeat('gold_filter')
            if not gold_filter.ensure_min_gold_before_attack(screen_state.wait_for_army_ready_screen):
                wait_failure = screen_state.consume_last_wait_failure()
                if wait_failure and wait_failure.get('code') in ('guard_retry_limit', 'guard_timeout'):
                    issue = RecoveryIssue(wait_failure.get('code', 'guard_retry_limit'), wait_failure.get('details', 'loot reroll lost battle screen'))
                    if watchdog.handle_issue(issue):
                        pyautogui.sleep(1)
                        continue
                telegram_reporter.append_console_log('Gold filter rerolled target.')
                pyautogui.sleep(1)
                continue

            watchdog.heartbeat('deploy_start')
            telegram_reporter.append_console_log(f'Attack #{check_storages_full.counter + 1} deploy started.')
            attack.report_base_before_attack(attack_number=check_storages_full.counter + 1)
            watchdog.heartbeat('align_screen')
            attack.align_screen()
            watchdog.heartbeat('deploy_troops')
            attack.deploy_troops()
            watchdog.heartbeat('surrender')
            surrender_ok = attack.surrender()
            if not surrender_ok:
                go_home_failure = attack.consume_last_go_home_failure()
                issue = RecoveryIssue(
                    (go_home_failure or {}).get('code', 'guard_retry_limit'),
                    (go_home_failure or {}).get('details', 'go-home button not found during surrender'),
                )
                if watchdog.handle_issue(issue):
                    pyautogui.sleep(1)
                    continue
                pyautogui.sleep(1)
                continue
            watchdog.heartbeat('post_battle_okay')
            handle_okay_after_battle()
            watchdog.heartbeat('post_attack')
            telegram_reporter.append_console_log('Battle finished, returned home.')

            current_attack_count = check_storages_full.counter + 1
            try:
                state = runtime_state.record_attack()
                current_attack_count = int(state.get('attack_count', current_attack_count))
                try:
                    telegram_reporter.upsert_attack_log_message(
                        f"Было атак: {current_attack_count}"
                    )
                except Exception as exc:
                    print(f"Attack log update failed: {exc}")
            except OSError as exc:
                print(f"Runtime state update failed: {exc}")

            if (
                lcfg.get_bool('ENABLE_STORAGE_MONITOR', True)
                and current_attack_count > 0
                and current_attack_count % lcfg.get_int('STORAGE_MONITOR_EVERY_ATTACKS', 20) == 0
            ):
                watchdog.heartbeat('storage_monitor')
                storage_payload = storage_monitor.storages_are_full()
                if bool(storage_payload.get('full')):
                    storage_monitor.notify_full_storages(storage_payload)
                    break

            if (
                runtime_state.wall_key_cycle_enabled(default=bool(getattr(cfg, 'ENABLE_WALL_KEY_CYCLE', True)))
                and current_attack_count > 0
                and current_attack_count % int(
                    runtime_state.get_wall_key_cycle_every_override(
                        default=int(getattr(cfg, 'WALL_KEY_CYCLE_EVERY_ATTACKS', 5))
                    )
                ) == 0
            ):
                wall_cycle_key = lcfg.get_str('WALL_KEY_CYCLE_KEY', '-').strip() or '-'
                wall_cycle_duration = max(0.0, lcfg.get_float('WALL_KEY_CYCLE_DURATION_SECONDS', 95.0))
                telegram_reporter.append_console_log(
                    f'Wall key cycle start after {current_attack_count} attacks: align_wall_screen -> key={wall_cycle_key} wait={wall_cycle_duration:.0f}s.'
                )
                watchdog.heartbeat('wall_cycle_align')
                attack.align_wall_screen()
                watchdog.heartbeat('wall_cycle_run')
                pyautogui.press(wall_cycle_key)
                if wall_cycle_duration > 0:
                    pyautogui.sleep(wall_cycle_duration)
                telegram_reporter.append_console_log('Wall key cycle finished, returning to main loop.')

            storages_full = check_storages_full()
            if storages_full:
                print("Storages are full. Stopping the bot.")
                telegram_reporter.append_console_log('Synthetic storage limit reached, bot stopped.')
                break
        except Exception as exc:
            issue = RecoveryIssue(
                'unexpected_exception',
                f'{type(exc).__name__}: {exc} (stage={watchdog.last_stage})',
            )
            print(f'Unexpected bot error: {issue.details}')
            if watchdog.handle_issue(issue):
                pyautogui.sleep(1)
                continue
            pyautogui.sleep(1)

def parse_args():
    return argparse.ArgumentParser().parse_args()

if __name__ == "__main__":
    parse_args()
    main()
