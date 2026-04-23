import config as cfg
import runtime_state
from attack_runtime.spell_modes import spell_mode_label
from bot_config_schema import CATEGORY_META, build_setting_button_text, category_ids, category_meta, settings_for_category


def ui_mode():
    mode = str(getattr(cfg, 'TELEGRAM_UI_MODE', 'default')).strip().lower()
    return 'test' if mode == 'test' else 'default'


def root_menu():
    wall_enabled = runtime_state.wall_key_cycle_enabled(
        default=bool(getattr(cfg, 'ENABLE_WALL_KEY_CYCLE', True))
    )
    wall_every = runtime_state.get_wall_key_cycle_every_override(
        default=int(getattr(cfg, 'WALL_KEY_CYCLE_EVERY_ATTACKS', 5))
    )
    rows = [
        [
            {'text': '🟢 Старт', 'callback_data': 'start_bot'},
            {'text': '🔴 Стоп', 'callback_data': 'stop_bot'},
        ],
        [
            {'text': '🎮 Управление', 'callback_data': 'menu_control'},
            {'text': '👤 Аккаунты', 'callback_data': 'menu_accounts'},
        ],
        [
            {'text': '✨ Спеллы', 'callback_data': 'menu_spells'},
            {'text': '⚙️ Конфиг', 'callback_data': 'menu_config'},
        ],
        [
            {'text': '⌨️ Ввод', 'callback_data': 'menu_input'},
        ],
        [
            {'text': '🖥️ Режим консоли', 'callback_data': 'toggle_console'},
            {'text': '📷 Скриншот', 'callback_data': 'send_screenshot'},
        ],
        [
            {'text': f'Проходка стен: {"✅" if wall_enabled else "❌"}', 'callback_data': 'toggle_wall_cycle'},
        ],
        [
            {'text': f'{int(wall_every)} боев', 'callback_data': 'open_wall_cycle_every'},
        ],
        [
            {'text': '📦 Заполнить хранилища везде', 'callback_data': 'fill_storages_everywhere'},
        ],
    ]
    return {'inline_keyboard': rows}


def control_menu():
    rows = [
        [
            {'text': '📸 Скрины', 'callback_data': 'open_screenshots'},
            {'text': '🛟 Recovery', 'callback_data': 'recovery_debug'},
        ],
        [
            {'text': '🔁 Выйти с игры', 'callback_data': 'restart_game_only'},
            {'text': '↩️ Вернуться в игру', 'callback_data': 'return_to_game'},
        ],
        [
            {'text': '⬅️ Назад', 'callback_data': 'show_panel'},
        ],
    ]
    return {'inline_keyboard': rows}


SPELLS_MENU = {
    'inline_keyboard': [
        [
            {'text': '🪨 stoneDick', 'callback_data': 'spell_stonedick'},
            {'text': '💥 crazyWalls', 'callback_data': 'spell_crazywalls'},
        ],
        [
            {'text': '⬅️ Назад', 'callback_data': 'show_panel'},
        ],
    ]
}

INPUT_MENU = {
    'inline_keyboard': [
        [
            {'text': '🖥️ Input Default', 'callback_data': 'input_default'},
        ],
        [
            {'text': '⬅️ Назад', 'callback_data': 'show_panel'},
        ],
    ]
}


def accounts_menu():
    return {
        'inline_keyboard': [
            [
                {'text': 'old_proxima', 'callback_data': 'account_pick:old_proxima'},
                {'text': 'yung_proxima', 'callback_data': 'account_pick:yung_proxima'},
            ],
            [
                {'text': 'proxima', 'callback_data': 'account_pick:proxima'},
                {'text': 'samgold', 'callback_data': 'account_pick:samgold'},
            ],
            [
                {'text': 'love12steps', 'callback_data': 'account_pick:love12steps'},
            ],
            [
                {'text': '⬅️ Назад', 'callback_data': 'show_panel'},
            ],
        ]
    }


def config_root_menu():
    rows = []
    categories = category_ids()
    for index in range(0, len(categories), 2):
        row = []
        for category_id in categories[index:index + 2]:
            row.append({'text': category_meta(category_id)['label'], 'callback_data': f'config_cat:{category_id}'})
        rows.append(row)
    rows.append([{'text': '⬅️ Назад', 'callback_data': 'show_panel'}])
    return {'inline_keyboard': rows}


def config_category_menu(category_id):
    rows = []
    for setting_id in settings_for_category(category_id):
        callback_prefix = 'config_edit'
        from bot_config_schema import get_setting_meta
        meta = get_setting_meta(setting_id)
        if meta['type'] in ('bool', 'enum'):
            callback_prefix = 'config_toggle'
        rows.append([
            {'text': build_setting_button_text(setting_id), 'callback_data': f'{callback_prefix}:{setting_id}'}
        ])
    rows.append([
        {'text': '⬅️ К категориям', 'callback_data': 'menu_config'},
        {'text': '🏠 На главную', 'callback_data': 'show_panel'},
    ])
    return {'inline_keyboard': rows}


def keyboard_for_view(view_name):
    normalized = str(view_name or 'root').strip().lower()
    if normalized == 'config_root':
        return config_root_menu()
    if normalized.startswith('config_cat:'):
        return config_category_menu(normalized.split(':', 1)[1])
    mapping = {
        'root': root_menu(),
        'control': control_menu(),
        'spells': SPELLS_MENU,
        'input': INPUT_MENU,
        'accounts': accounts_menu(),
    }
    return mapping.get(normalized, root_menu())


def runtime_status_text(controller):
    running = controller.is_running()
    spell_mode = runtime_state.get_spell_mode(
        default=getattr(cfg, 'SPELL_MODE_DEFAULT', 'stoneDick')
    )
    status_emoji = '🟢' if running else '🔴'
    separator = '================' if running else '========'
    return (
        f'Clash Of Clans autobot backup v9 {status_emoji}\n'
        f'{separator}\n'
        f"Режим спеллов: {spell_mode_label(spell_mode)}\n"
        f"Проходка стен: {'✅' if runtime_state.wall_key_cycle_enabled(default=bool(getattr(cfg, 'ENABLE_WALL_KEY_CYCLE', True))) else '❌'}\n"
        f"После боев: {int(runtime_state.get_wall_key_cycle_every_override(default=int(getattr(cfg, 'WALL_KEY_CYCLE_EVERY_ATTACKS', 5))))}\n"
        f"Аккаунт: {runtime_state.get_current_account() or 'не определен'}\n"
        'Режим: 🛡️ default\n'
        'Ввод: 🖥️ default'
    )


def build_status_message(controller):
    return runtime_status_text(controller)


def config_root_text():
    return (
        '⚙️ Конфиг бота\n'
        '────────────\n'
        'Здесь собраны рабочие настройки, которые можно менять без входа в код.\n'
        'Открой категорию, нажми на параметр и введи новое значение сообщением.'
    )


def config_category_text(category_id):
    meta = CATEGORY_META[category_id]
    count = len(settings_for_category(category_id))
    return (
        f"{meta['label']}\n"
        '────────────\n'
        f"{meta['description']}\n"
        f'Параметров в разделе: {count}\n'
        'Кнопка показывает текущее значение. Переключатели меняются по нажатию, числа и регионы бот попросит ввести сообщением.'
    )


def screenshot_setting_keyboard():
    return {
        'inline_keyboard': [
            [
                {'text': '🚫 Off', 'callback_data': 'shots_off'},
                {'text': '⬅️ Назад', 'callback_data': 'menu_control'},
            ],
            [
                {'text': '🏠 На главную', 'callback_data': 'show_panel'},
            ],
        ]
    }


def screenshot_setting_text():
    override = runtime_state.get_battle_report_every_override(
        default=int(getattr(cfg, 'BATTLE_REPORT_EVERY', 15))
    )
    if override is None or int(override) <= 0:
        current = 'off'
    else:
        current = f'каждые {int(override)} боев'
    return (
        '📸 Боевые скрины\n'
        '────────────\n'
        f'Текущее: {current}\n'
        'Введи число сообщением.\n'
        'Пример: 5, 15, 30\n'
        'Чтобы выключить: off'
    )


def wall_cycle_setting_text():
    every = runtime_state.get_wall_key_cycle_every_override(
        default=int(getattr(cfg, 'WALL_KEY_CYCLE_EVERY_ATTACKS', 5))
    )
    return (
        '🧱 Проходка стен\n'
        '────────────\n'
        f'Текущее: после {int(every)} боев\n'
        'Введи число сообщением.\n'
        'Пример: 5, 10, 20'
    )


def accounts_menu_text(current_account=None):
    return (
        '👤 Аккаунты\n'
        '────────────\n'
        f'Текущий аккаунт: {current_account or "не удалось определить"}\n'
        'Выбери аккаунт ниже. Бот вернется домой, откроет список аккаунтов, найдет нужный и подтвердит вход на базу.'
    )
