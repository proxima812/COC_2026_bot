from __future__ import annotations

import asyncio
import subprocess
import time
from typing import Optional

import pyautogui
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import attack
import account_switcher
import config as cfg
import runtime_state
import telegram_reporter
from attack_runtime.spell_modes import spell_mode_label
from bot_config_schema import build_setting_prompt_text, get_setting_meta, set_setting_value, toggle_setting
from telegram_ui.presentation import (
    accounts_menu_text,
    build_status_message,
    config_category_text,
    config_root_text,
    keyboard_for_view,
    screenshot_setting_keyboard,
    screenshot_setting_text,
    wall_cycle_setting_text,
)
from telegram_ui.process_controller import BotProcessController

router = Router()
controller = BotProcessController()
MESSAGE_AUTO_DELETE_SECONDS = 10
fill_storages_everywhere_task: Optional[asyncio.Task] = None


def _read_required_telegram_config():
    token = getattr(cfg, 'TELEGRAM_BOT_TOKEN', '').strip()
    allowed_chat_ids = tuple(
        str(chat_id).strip()
        for chat_id in getattr(cfg, 'TELEGRAM_ALLOWED_CHAT_IDS', ())
        if str(chat_id).strip()
    )
    if not token:
        raise ValueError('TELEGRAM_BOT_TOKEN не задан (ожидается в .env)')
    if not allowed_chat_ids:
        raise ValueError('TELEGRAM_ALLOWED_CHAT_IDS не заданы (ожидается в .env/config)')
    return token, allowed_chat_ids


def _is_allowed(chat_id: int | str, allowed_chat_ids) -> bool:
    normalized = str(chat_id)
    return normalized in {str(item).strip() for item in (allowed_chat_ids or ()) if str(item).strip()}


def _inline_markup(raw_markup):
    if raw_markup is None:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=item['text'], callback_data=item['callback_data']) for item in row]
            for row in raw_markup['inline_keyboard']
        ]
    )


def _parse_screenshot_every(raw_text):
    text = str(raw_text or '').strip().lower()
    if not text:
        return None
    if text in ('off', 'disable', 'disabled', 'нет', 'выкл'):
        return 0
    try:
        value = int(float(text))
    except (TypeError, ValueError):
        return None
    if value < 0 or value > 10000:
        return None
    return value


def _recovery_debug_text():
    event = runtime_state.get_last_recovery_event()
    return (
        '🛟 Recovery debug\n'
        '────────────\n'
        f'Последний issue: {event.get("issue_code") or "еще не было"}\n'
        f'Детали: {event.get("issue_details") or "нет данных"}\n'
        f'Последнее действие: {event.get("action") or "нет данных"}\n'
        f'Время: {event.get("time") or "нет данных"}'
    )


def _console_status_text():
    enabled = runtime_state.telegram_console_enabled(default=False)
    lines = runtime_state.get_telegram_console_lines()
    return (
        '🖥️ Console mode\n'
        '────────────\n'
        f'Статус: {"ON" if enabled else "OFF"}\n'
        f'Строк в логе: {len(lines)}'
    )


async def _send_live_screenshot(chat_id: int | str):
    try:
        screenshot = pyautogui.screenshot()
    except Exception as exc:
        return f'Скриншот не удалось сделать: {exc}'
    sent = telegram_reporter.send_battle_screenshot(screenshot, cycle_number=None, caption_prefix='Live screenshot')
    return 'Текущий скриншот отправлен.' if sent else 'Скриншот не удалось отправить в Telegram.'


def _panel_text_for_view(view_name: str):
    normalized = str(view_name or 'root').strip().lower()
    if normalized == 'config_root':
        return config_root_text()
    if normalized.startswith('config_cat:'):
        category_id = normalized.split(':', 1)[1]
        try:
            return config_category_text(category_id)
        except Exception:
            return config_root_text()
    if normalized == 'accounts':
        return accounts_menu_text(runtime_state.get_current_account())
    return build_status_message(controller)


def _clear_pending_input():
    runtime_state.clear_timing_pending_item_id()


async def _edit_or_send_panel(bot: Bot, chat_id: int | str, text: str):
    current_keyboard = _inline_markup(keyboard_for_view(runtime_state.get_telegram_panel_view(default='root')))
    existing_message_id = runtime_state.get_telegram_control_message_id()
    if existing_message_id is not None:
        try:
            await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=existing_message_id,
                reply_markup=current_keyboard,
                parse_mode='HTML',
            )
            return existing_message_id
        except Exception as exc:
            if 'message is not modified' in str(exc).lower():
                return existing_message_id
            runtime_state.clear_telegram_control_message_id()
    message = await bot.send_message(chat_id=chat_id, text=text, reply_markup=current_keyboard, parse_mode='HTML')
    runtime_state.set_telegram_control_message_id(message.message_id)
    return message.message_id


async def _edit_or_send_message(bot: Bot, chat_id: int | str, text: str, reply_markup=None):
    existing_message_id = runtime_state.get_telegram_control_message_id()
    if existing_message_id is not None:
        try:
            await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=existing_message_id,
                reply_markup=reply_markup,
                parse_mode='HTML',
            )
            return existing_message_id
        except Exception as exc:
            if 'message is not modified' in str(exc).lower():
                return existing_message_id
            runtime_state.clear_telegram_control_message_id()
    message = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')
    runtime_state.set_telegram_control_message_id(message.message_id)
    return message.message_id


async def _apply_status_message(bot: Bot, chat_id: int | str, prefix: Optional[str] = None):
    text = build_status_message(controller)
    if prefix:
        text = f'{prefix}\n{text}'
    await _edit_or_send_panel(bot, chat_id, text)


async def _render_current_panel(bot: Bot, chat_id: int | str, prefix: Optional[str] = None):
    text = _panel_text_for_view(runtime_state.get_telegram_panel_view(default='root'))
    if prefix:
        text = f'{prefix}\n\n{text}'
    await _edit_or_send_panel(bot, chat_id, text)


async def _send_fresh_panel(bot: Bot, chat_id: int | str, prefix: Optional[str] = None):
    runtime_state.clear_telegram_control_message_id()
    text = _panel_text_for_view(runtime_state.get_telegram_panel_view(default='root'))
    if prefix:
        text = f'{prefix}\n{text}'
    await _edit_or_send_panel(bot, chat_id, text)


async def _cleanup_stop_side_effects(bot: Bot, chat_id: int | str):
    for getter, clearer in (
        (runtime_state.get_telegram_attack_log_message_id, runtime_state.clear_telegram_attack_log_message_id),
        (runtime_state.get_telegram_console_message_id, runtime_state.clear_telegram_console_message_id),
    ):
        message_id = getter()
        if message_id is not None:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception:
                pass
        clearer()
    for message_id in runtime_state.get_telegram_battle_screenshot_message_ids():
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            pass
    runtime_state.clear_telegram_battle_screenshot_message_ids()
    runtime_state.clear_telegram_console_lines()


def _fill_storages_running():
    return fill_storages_everywhere_task is not None and not fill_storages_everywhere_task.done()


async def _cancel_fill_storages_everywhere(bot: Bot, chat_id: int | str, reason: Optional[str] = None):
    global fill_storages_everywhere_task
    task = fill_storages_everywhere_task
    if task is None or task.done():
        fill_storages_everywhere_task = None
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    fill_storages_everywhere_task = None
    if reason:
        await _apply_status_message(bot, chat_id, reason)


async def _run_fill_storages_everywhere(bot: Bot, chat_id: int | str):
    previous_wall_enabled = runtime_state.wall_key_cycle_enabled(
        default=bool(getattr(cfg, 'ENABLE_WALL_KEY_CYCLE', True))
    )
    accounts = tuple(getattr(cfg, 'FILL_STORAGES_ACCOUNT_SEQUENCE', ('proxima', 'old_proxima', 'yung_proxima', 'samgold')))
    attacks_per_account = max(1, int(getattr(cfg, 'FILL_STORAGES_ATTACKS_PER_ACCOUNT', 50)))
    poll_interval = max(0.5, float(getattr(cfg, 'FILL_STORAGES_POLL_INTERVAL_SECONDS', 2.0)))

    runtime_state.set_wall_key_cycle_enabled(False)
    await _apply_status_message(
        bot,
        chat_id,
        f'Запускаю сценарий заполнения хранилищ.\nПроходка стен временно выключена.\nАккаунтов в очереди: {len(accounts)}.',
    )

    try:
        for index, account_name in enumerate(accounts, start=1):
            if controller.is_running():
                _ok, _response_text = controller.stop()
                await _cleanup_stop_side_effects(bot, chat_id)

            await _apply_status_message(
                bot,
                chat_id,
                f'[{index}/{len(accounts)}] Переключаюсь на аккаунт <b>{account_name}</b>.',
            )
            switch_result = account_switcher.switch_account(account_name)
            if switch_result.account_name:
                runtime_state.set_current_account(switch_result.account_name)
            if not switch_result.ok:
                await _apply_status_message(
                    bot,
                    chat_id,
                    f'Сценарий остановлен.\n{switch_result.message}',
                )
                return

            _ok, response_text = controller.start()
            if not _ok:
                await _apply_status_message(
                    bot,
                    chat_id,
                    f'Не удалось запустить бот на аккаунте <b>{account_name}</b>.\n{response_text}',
                )
                return

            await _apply_status_message(
                bot,
                chat_id,
                f'Аккаунт <b>{account_name}</b>: запускаю {attacks_per_account} атак.',
            )

            while True:
                await asyncio.sleep(poll_interval)
                if not controller.is_running():
                    current_attacks = int(runtime_state.load_state().get('attack_count', 0))
                    await _apply_status_message(
                        bot,
                        chat_id,
                        f'Бот остановился раньше времени на аккаунте <b>{account_name}</b>.\n'
                        f'Атак выполнено: {current_attacks}/{attacks_per_account}.',
                    )
                    return

                current_attacks = int(runtime_state.load_state().get('attack_count', 0))
                if current_attacks >= attacks_per_account:
                    _ok, _response_text = controller.stop()
                    await _cleanup_stop_side_effects(bot, chat_id)
                    await _apply_status_message(
                        bot,
                        chat_id,
                        f'Аккаунт <b>{account_name}</b>: {current_attacks} атак завершены.',
                    )
                    break

        if controller.is_running():
            _ok, _response_text = controller.stop()
            await _cleanup_stop_side_effects(bot, chat_id)
        _force_stop_game()
        await _apply_status_message(bot, chat_id, 'Все готово, вождь!\nВсе аккаунты отработали по 50 атак, игра закрыта.')
    except asyncio.CancelledError:
        if controller.is_running():
            _ok, _response_text = controller.stop()
            await _cleanup_stop_side_effects(bot, chat_id)
        await _apply_status_message(bot, chat_id, 'Сценарий заполнения хранилищ остановлен.')
        raise
    finally:
        runtime_state.set_wall_key_cycle_enabled(previous_wall_enabled)


def _show_panel_view_name(view_name: str):
    runtime_state.set_telegram_panel_view(view_name)


async def _delete_message_later(bot: Bot, chat_id: int | str, message_id: int, delay_seconds: int = MESSAGE_AUTO_DELETE_SECONDS):
    try:
        await asyncio.sleep(max(0, int(delay_seconds)))
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


def _schedule_message_delete(bot: Bot, chat_id: int | str, message_id: Optional[int], delay_seconds: int = MESSAGE_AUTO_DELETE_SECONDS):
    if message_id is None:
        return
    asyncio.create_task(_delete_message_later(bot, chat_id, int(message_id), delay_seconds))


def _schedule_incoming_delete(bot: Bot, message: Message):
    _schedule_message_delete(bot, message.chat.id, getattr(message, 'message_id', None))


def _adb_run(args, timeout=8.0):
    adb_bin = str(getattr(cfg, 'ADB_INPUT_BIN', '')).strip()
    if not adb_bin:
        return False, 'ADB_INPUT_BIN not configured'
    command = [adb_bin]
    serial = str(getattr(cfg, 'ADB_DEVICE_SERIAL', '')).strip()
    if serial:
        command.extend(['-s', serial])
    command.extend(args)
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=timeout,
        )
    except Exception as exc:
        return False, str(exc)
    output = (completed.stdout or b'').decode('utf-8', errors='ignore').strip()
    error = (completed.stderr or b'').decode('utf-8', errors='ignore').strip()
    if completed.returncode != 0:
        return False, error or output or f'return code {completed.returncode}'
    return True, output


def _prepare_adb():
    _adb_run(['start-server'], timeout=6)
    ports = str(getattr(cfg, 'ADB_CONNECT_PORTS', '5555 5556 5565 5575 5585')).strip().split()
    for port in ports:
        _adb_run(['connect', f'127.0.0.1:{port}'], timeout=3)
    device_timeout = max(5.0, float(getattr(cfg, 'RECOVERY_ADB_DEVICE_TIMEOUT_SECONDS', 40.0)))
    started = time.monotonic()
    while time.monotonic() - started < device_timeout:
        ok, out = _adb_run(['devices'], timeout=3)
        if ok and '\tdevice' in out:
            return True
        time.sleep(1.0)
    return False


def _force_stop_game():
    package_name = str(getattr(cfg, 'COC_PACKAGE_NAME', 'com.supercell.clashofclans')).strip() or 'com.supercell.clashofclans'
    if not _prepare_adb():
        return False, 'ADB device not ready'
    ok, out = _adb_run(['shell', 'am', 'force-stop', package_name], timeout=6)
    return ok, out or 'Игра закрыта.'


def _launch_game():
    package_name = str(getattr(cfg, 'COC_PACKAGE_NAME', 'com.supercell.clashofclans')).strip() or 'com.supercell.clashofclans'
    if not _prepare_adb():
        return False, 'ADB device not ready'
    ok, out = _adb_run(
        ['shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'],
        timeout=8,
    )
    if not ok:
        return False, out
    time.sleep(max(1.0, float(getattr(cfg, 'RECOVERY_POST_LAUNCH_SLEEP_SECONDS', 8.0))))
    return True, 'Игра запущена.'


@router.message(Command('start'))
async def cmd_start(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        _show_panel_view_name('root')
        await _send_fresh_panel(bot, message.chat.id)


@router.message(Command('status'))
async def cmd_status(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        _show_panel_view_name('root')
        await _apply_status_message(bot, message.chat.id)


@router.message(Command('run'))
async def cmd_run(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        _ok, response_text = controller.start()
        await _apply_status_message(bot, message.chat.id, response_text)


@router.message(Command('stop'))
async def cmd_stop(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        _ok, response_text = controller.stop()
        await _cleanup_stop_side_effects(bot, message.chat.id)
        await _apply_status_message(bot, message.chat.id, response_text)


@router.message(Command('config'))
async def cmd_config(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        _show_panel_view_name('config_root')
        await _render_current_panel(bot, message.chat.id)


@router.message(Command('recovery_debug'))
async def cmd_recovery_debug(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        _show_panel_view_name('control')
        await _edit_or_send_panel(bot, message.chat.id, _recovery_debug_text())


@router.message(Command('screenshot'))
async def cmd_screenshot(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        await _apply_status_message(bot, message.chat.id, await _send_live_screenshot(message.chat.id))


@router.message(Command('shots'))
async def cmd_shots(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        runtime_state.set_timing_pending_item_id('shots')
        runtime_state.set_telegram_panel_view('control')
        await _edit_or_send_message(bot, message.chat.id, screenshot_setting_text(), reply_markup=_inline_markup(screenshot_setting_keyboard()))


@router.message(Command('console'))
async def cmd_console(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        enabled = not runtime_state.telegram_console_enabled(default=False)
        runtime_state.set_telegram_console_enabled(enabled)
        if enabled:
            runtime_state.clear_telegram_console_lines()
            telegram_reporter.append_console_log('Console mode enabled.')
        else:
            runtime_state.clear_telegram_console_lines()
        await _apply_status_message(bot, message.chat.id, f'Режим консоли {"включен" if enabled else "выключен"}.\n{_console_status_text()}')


@router.message(Command('spell_stonedick'))
async def cmd_spell_stonedick(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        runtime_state.set_spell_mode('stoneDick')
        await _apply_status_message(bot, message.chat.id, f'Режим спеллов {spell_mode_label("stoneDick")} включен.')


@router.message(Command('spell_crazywalls'))
async def cmd_spell_crazywalls(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        runtime_state.set_spell_mode('crazyWalls')
        await _apply_status_message(bot, message.chat.id, f'Режим спеллов {spell_mode_label("crazyWalls")} включен.')


@router.message(Command('input_default'))
async def cmd_input_default(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        runtime_state.set_input_profile('default')
        await _apply_status_message(bot, message.chat.id, 'Профиль ввода default включен.')


@router.message(Command('wall'))
async def cmd_wall(message: Message, bot: Bot, allowed_chat_ids):
    if _is_allowed(message.chat.id, allowed_chat_ids):
        _schedule_incoming_delete(bot, message)
        _clear_pending_input()
        attack.align_wall_screen()
        await _apply_status_message(bot, message.chat.id, 'Команда /wall выполнена: обратный align_screen применен.')


@router.message(F.text)
async def handle_text_input(message: Message, bot: Bot, allowed_chat_ids):
    if not _is_allowed(message.chat.id, allowed_chat_ids):
        return
    _schedule_incoming_delete(bot, message)
    text = (message.text or '').strip()
    if not text or text.startswith('/'):
        return

    pending = runtime_state.get_timing_pending_item_id()

    if pending == 'shots':
        parsed_value = _parse_screenshot_every(text)
        markup = _inline_markup(screenshot_setting_keyboard())
        if parsed_value is None:
            await _edit_or_send_message(bot, message.chat.id, f'Некорректное значение: "{text}". Используй число боев или off.\n\n{screenshot_setting_text()}', reply_markup=markup)
            return
        runtime_state.set_battle_report_every_override(parsed_value)
        runtime_state.clear_timing_pending_item_id()
        _show_panel_view_name('root')
        await _apply_status_message(bot, message.chat.id, 'Настройка боевых скринов обновлена.')
        return

    if pending == 'wall_cycle_every':
        try:
            parsed_value = int(float(text))
        except (TypeError, ValueError):
            await _edit_or_send_message(bot, message.chat.id, f'Некорректное значение: "{text}".\n\n{wall_cycle_setting_text()}')
            return
        if parsed_value <= 0 or parsed_value > 10000:
            await _edit_or_send_message(bot, message.chat.id, f'Некорректное значение: "{text}".\n\n{wall_cycle_setting_text()}')
            return
        runtime_state.set_wall_key_cycle_every_override(parsed_value)
        runtime_state.clear_timing_pending_item_id()
        _show_panel_view_name('root')
        await _apply_status_message(bot, message.chat.id, f'Проходка стен теперь после {parsed_value} боев.')
        return

    if pending and pending.startswith('config:'):
        setting_id = pending.split(':', 1)[1]
        try:
            set_setting_value(setting_id, text)
        except Exception:
            await _edit_or_send_message(
                bot,
                message.chat.id,
                f'Некорректное значение: "{text}".\n\n{build_setting_prompt_text(setting_id)}',
            )
            return
        runtime_state.clear_timing_pending_item_id()
        meta = get_setting_meta(setting_id)
        await _render_current_panel(bot, message.chat.id, f'Обновлено: {meta["label"]}.')
        return


@router.callback_query(F.data.startswith('config_cat:'))
async def config_category_callback(query: CallbackQuery, bot: Bot, allowed_chat_ids):
    if not query.message or not _is_allowed(query.message.chat.id, allowed_chat_ids):
        return
    try:
        await query.answer()
    except Exception:
        pass
    _clear_pending_input()
    category_id = (query.data or '').split(':', 1)[1]
    _show_panel_view_name(f'config_cat:{category_id}')
    await _render_current_panel(bot, query.message.chat.id)


@router.callback_query(F.data.startswith('config_toggle:'))
async def config_toggle_callback(query: CallbackQuery, bot: Bot, allowed_chat_ids):
    if not query.message or not _is_allowed(query.message.chat.id, allowed_chat_ids):
        return
    try:
        await query.answer()
    except Exception:
        pass
    _clear_pending_input()
    setting_id = (query.data or '').split(':', 1)[1]
    try:
        toggle_setting(setting_id)
    except Exception:
        await _render_current_panel(bot, query.message.chat.id, 'Не удалось изменить настройку.')
        return
    meta = get_setting_meta(setting_id)
    await _render_current_panel(bot, query.message.chat.id, f'Обновлено: {meta["label"]}.')


@router.callback_query(F.data.startswith('config_edit:'))
async def config_edit_callback(query: CallbackQuery, bot: Bot, allowed_chat_ids):
    if not query.message or not _is_allowed(query.message.chat.id, allowed_chat_ids):
        return
    try:
        await query.answer()
    except Exception:
        pass
    setting_id = (query.data or '').split(':', 1)[1]
    runtime_state.set_timing_pending_item_id(f'config:{setting_id}')
    await _edit_or_send_message(bot, query.message.chat.id, build_setting_prompt_text(setting_id))


@router.callback_query(F.data.in_({
    'show_panel', 'menu_control', 'menu_spells', 'menu_input', 'menu_config', 'menu_accounts',
    'start_bot', 'stop_bot', 'recovery_debug',
    'send_screenshot', 'toggle_console', 'spell_stonedick', 'spell_crazywalls',
    'toggle_wall_cycle', 'open_wall_cycle_every',
    'input_default', 'open_screenshots', 'shots_off',
    'restart_game_only', 'return_to_game',
    'fill_storages_everywhere',
}))
async def callback_router(query: CallbackQuery, bot: Bot, allowed_chat_ids):
    if not query.message or not _is_allowed(query.message.chat.id, allowed_chat_ids):
        return
    data = query.data or ''
    try:
        await query.answer()
    except Exception:
        pass

    if data == 'show_panel':
        _clear_pending_input()
        _show_panel_view_name('root')
        await _apply_status_message(bot, query.message.chat.id)
        return
    if data == 'menu_control':
        _clear_pending_input()
        _show_panel_view_name('control')
        await _render_current_panel(bot, query.message.chat.id)
        return
    if data == 'menu_spells':
        _clear_pending_input()
        _show_panel_view_name('spells')
        await _render_current_panel(bot, query.message.chat.id)
        return
    if data == 'menu_input':
        _clear_pending_input()
        _show_panel_view_name('input')
        await _render_current_panel(bot, query.message.chat.id)
        return
    if data == 'menu_config':
        _clear_pending_input()
        _show_panel_view_name('config_root')
        await _render_current_panel(bot, query.message.chat.id)
        return
    if data == 'menu_accounts':
        _clear_pending_input()
        _show_panel_view_name('accounts')
        detected = account_switcher.detect_current_account()
        runtime_state.set_current_account(detected)
        await _edit_or_send_panel(bot, query.message.chat.id, accounts_menu_text(detected))
        return
    if data == 'open_screenshots':
        runtime_state.set_timing_pending_item_id('shots')
        runtime_state.set_telegram_panel_view('control')
        await _edit_or_send_message(bot, query.message.chat.id, screenshot_setting_text(), reply_markup=_inline_markup(screenshot_setting_keyboard()))
        return
    if data == 'open_wall_cycle_every':
        runtime_state.set_timing_pending_item_id('wall_cycle_every')
        runtime_state.set_telegram_panel_view('root')
        await _edit_or_send_message(bot, query.message.chat.id, f'Сколько боев поставить для проходки стен?\n\n{wall_cycle_setting_text()}')
        return
    if data == 'shots_off':
        _clear_pending_input()
        runtime_state.set_battle_report_every_override(0)
        await _edit_or_send_message(bot, query.message.chat.id, f'Боевые скрины выключены.\n\n{screenshot_setting_text()}', reply_markup=_inline_markup(screenshot_setting_keyboard()))
        return
    if data == 'start_bot':
        _clear_pending_input()
        if _fill_storages_running():
            await _apply_status_message(bot, query.message.chat.id, 'Сначала останови сценарий "Заполнить хранилища везде".')
            return
        _ok, response_text = controller.start()
        await _apply_status_message(bot, query.message.chat.id, response_text)
        return
    if data == 'stop_bot':
        _clear_pending_input()
        if _fill_storages_running():
            await _cancel_fill_storages_everywhere(bot, query.message.chat.id, 'Сценарий "Заполнить хранилища везде" остановлен.')
            return
        _ok, response_text = controller.stop()
        await _cleanup_stop_side_effects(bot, query.message.chat.id)
        await _apply_status_message(bot, query.message.chat.id, response_text)
        return
    if data == 'recovery_debug':
        _clear_pending_input()
        _show_panel_view_name('control')
        await _edit_or_send_panel(bot, query.message.chat.id, _recovery_debug_text())
        return
    if data == 'restart_game_only':
        _clear_pending_input()
        ok, message = _force_stop_game()
        prefix = 'Игра закрыта через ADB.' if ok else f'Не удалось закрыть игру: {message}'
        _show_panel_view_name('control')
        await _render_current_panel(bot, query.message.chat.id, prefix)
        return
    if data == 'return_to_game':
        _clear_pending_input()
        ok, message = _launch_game()
        if not ok:
            _show_panel_view_name('control')
            await _render_current_panel(bot, query.message.chat.id, f'Не удалось запустить игру: {message}')
            return
        screenshot_status = await _send_live_screenshot(query.message.chat.id)
        _show_panel_view_name('control')
        await _render_current_panel(bot, query.message.chat.id, f'Игра запущена.\n{screenshot_status}')
        return
    if data == 'send_screenshot':
        _clear_pending_input()
        await _apply_status_message(bot, query.message.chat.id, await _send_live_screenshot(query.message.chat.id))
        return
    if data == 'toggle_console':
        _clear_pending_input()
        enabled = not runtime_state.telegram_console_enabled(default=False)
        runtime_state.set_telegram_console_enabled(enabled)
        if enabled:
            runtime_state.clear_telegram_console_lines()
            telegram_reporter.append_console_log('Console mode enabled.')
        else:
            runtime_state.clear_telegram_console_lines()
        await _apply_status_message(bot, query.message.chat.id, f'Режим консоли {"включен" if enabled else "выключен"}.\n{_console_status_text()}')
        return
    if data == 'toggle_wall_cycle':
        _clear_pending_input()
        enabled = not runtime_state.wall_key_cycle_enabled(default=bool(getattr(cfg, 'ENABLE_WALL_KEY_CYCLE', True)))
        runtime_state.set_wall_key_cycle_enabled(enabled)
        _show_panel_view_name('root')
        await _apply_status_message(bot, query.message.chat.id, 'Проходка стен включена.' if enabled else 'Проходка стен выключена.')
        return
    if data == 'fill_storages_everywhere':
        _clear_pending_input()
        global fill_storages_everywhere_task
        if _fill_storages_running():
            await _apply_status_message(bot, query.message.chat.id, 'Сценарий уже выполняется.')
            return
        fill_storages_everywhere_task = asyncio.create_task(_run_fill_storages_everywhere(bot, query.message.chat.id))
        return
    if data == 'spell_stonedick':
        _clear_pending_input()
        runtime_state.set_spell_mode('stoneDick')
        await _apply_status_message(bot, query.message.chat.id, f'Режим спеллов {spell_mode_label("stoneDick")} включен.')
        return
    if data == 'spell_crazywalls':
        _clear_pending_input()
        runtime_state.set_spell_mode('crazyWalls')
        await _apply_status_message(bot, query.message.chat.id, f'Режим спеллов {spell_mode_label("crazyWalls")} включен.')
        return
    if data == 'input_default':
        _clear_pending_input()
        runtime_state.set_input_profile('default')
        await _apply_status_message(bot, query.message.chat.id, 'Профиль ввода default включен.')


@router.callback_query(F.data.startswith('account_pick:'))
async def account_pick_callback(query: CallbackQuery, bot: Bot, allowed_chat_ids):
    if not query.message or not _is_allowed(query.message.chat.id, allowed_chat_ids):
        return
    try:
        await query.answer()
    except Exception:
        pass

    account_name = (query.data or '').split(':', 1)[1]
    prefix_lines = []
    _clear_pending_input()
    _show_panel_view_name('accounts')

    if controller.is_running():
        _ok, response_text = controller.stop()
        await _cleanup_stop_side_effects(bot, query.message.chat.id)
        prefix_lines.append(response_text)

    result = account_switcher.switch_account(account_name)
    if result.account_name:
        runtime_state.set_current_account(result.account_name)
    prefix_lines.append(result.message)
    await _edit_or_send_panel(
        bot,
        query.message.chat.id,
        '\n'.join(prefix_lines) + '\n\n' + accounts_menu_text(runtime_state.get_current_account()),
    )


async def _watch_process_exit(bot: Bot, primary_chat_id: str):
    while True:
        exit_event = controller.consume_exit_event()
        if exit_event:
            await _edit_or_send_panel(bot, primary_chat_id, f'{exit_event}\n{build_status_message(controller)}')
        await asyncio.sleep(1.0)


async def main():
    token, allowed_chat_ids = _read_required_telegram_config()
    primary_chat_id = allowed_chat_ids[0]
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    commands = [
        BotCommand(command='start', description='Панель управления'),
        BotCommand(command='run', description='Запустить основной цикл'),
        BotCommand(command='stop', description='Остановить процесс'),
        BotCommand(command='config', description='Открыть конфиг бота'),
        BotCommand(command='shots', description='Частота боевых скринов'),
        BotCommand(command='recovery_debug', description='Последний recovery issue/action'),
        BotCommand(command='screenshot', description='Отправить текущий скрин'),
        BotCommand(command='console', description='Вкл/выкл единый console log'),
        BotCommand(command='wall', description='Тестовый wall align'),
        BotCommand(command='spell_stonedick', description='Режим спеллов stoneDick'),
        BotCommand(command='spell_crazywalls', description='Режим спеллов crazyWalls'),
        BotCommand(command='input_default', description='Профиль ввода default'),
    ]
    await bot.set_my_commands(commands)
    _show_panel_view_name('root')
    await _edit_or_send_panel(bot, primary_chat_id, build_status_message(controller))
    asyncio.create_task(_watch_process_exit(bot, primary_chat_id))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), allowed_chat_ids=allowed_chat_ids)


if __name__ == '__main__':
    asyncio.run(main())
