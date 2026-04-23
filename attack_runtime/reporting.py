
import pyautogui

import config as cfg
import runtime_state
import telegram_reporter

def report_base_before_attack(attack_number=None):
    if attack_number is None:
        report_base_before_attack.counter += 1
        cycle_number = report_base_before_attack.counter
    else:
        cycle_number = int(attack_number)

    report_every = runtime_state.get_battle_report_every_override(
        default=int(getattr(cfg, 'BATTLE_REPORT_EVERY', 15))
    )
    if report_every is None or int(report_every) <= 0:
        return
    report_every = max(1, int(report_every))
    if cycle_number % report_every != 0:
        return

    if not (
        getattr(cfg, 'ENABLE_BATTLE_SCREENSHOTS', False)
        or getattr(cfg, 'ENABLE_TELEGRAM_REPORTS', False)
    ):
        return

    try:
        screenshot = pyautogui.screenshot()
    except Exception as exc:
        print(f'Battle screenshot failed: {exc}')
        return

    if getattr(cfg, 'SAVE_BATTLE_SCREENSHOTS_LOCAL', False):
        try:
            telegram_reporter.save_screenshot_local(screenshot, cycle_number=cycle_number)
        except Exception as exc:
            print(f'Local screenshot save failed: {exc}')

    if getattr(cfg, 'ENABLE_TELEGRAM_REPORTS', False):
        telegram_reporter.send_battle_screenshot(
            screenshot,
            cycle_number=cycle_number,
            caption_prefix='Clash of Clans base before attack',
        )

report_base_before_attack.counter = 0
