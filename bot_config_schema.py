import config as cfg
import live_config
import runtime_state
from attack_runtime.spell_modes import spell_mode_label

CATEGORY_META = {
    'attack': {
        'label': '⚔️ Атака',
        'description': 'Тайминги старта, высадки, героев и выхода из боя.',
    },
    'loot': {
        'label': '💰 Лут и OCR',
        'description': 'Фильтр золота и эликсира, reroll и debug OCR.',
    },
    'spells': {
        'label': '✨ Заклинания',
        'description': 'Режимы и параметры раскидки заклинаний.',
    },
    'wall': {
        'label': '🧱 Проходка стен',
        'description': 'Запуск wall macro по счетчику атак.',
    },
    'storage': {
        'label': '🏦 Хранилища',
        'description': 'Контроль заполнения хранилищ и остановка бота.',
    },
    'recovery': {
        'label': '🛟 Recovery',
        'description': 'Автовосстановление, таймауты и детект зависаний.',
    },
    'screen': {
        'label': '🖼️ Экраны',
        'description': 'Таймауты ожидания и частота проверок экранов.',
    },
}

SETTINGS = {
    'START_DELAY_SECONDS': {
        'category': 'attack', 'label': 'Стартовая задержка', 'icon': '⏱️', 'type': 'float', 'source': 'config',
        'description': 'Сколько секунд бот ждет перед началом цикла после запуска.', 'min': 0.0, 'max': 120.0,
    },
    'TROOP_SELECT_SLEEP': {
        'category': 'attack', 'label': 'Пауза выбора войск', 'icon': '🎯', 'type': 'float', 'source': 'timing',
        'description': 'Пауза после выбора типа войск.', 'min': 0.0, 'max': 10.0,
    },
    'DEPLOY_INTERVAL': {
        'category': 'attack', 'label': 'Интервал высадки', 'icon': '🚀', 'type': 'float', 'source': 'timing',
        'description': 'Пауза между отдельными нажатиями высадки.', 'min': 0.0, 'max': 5.0,
    },
    'HERO_DEPLOY_SLEEP': {
        'category': 'attack', 'label': 'Пауза героев', 'icon': '🦸', 'type': 'float', 'source': 'timing',
        'description': 'Пауза между выбором героя и его высадкой.', 'min': 0.0, 'max': 10.0,
    },
    'HERO_ABILITY_SLEEP': {
        'category': 'attack', 'label': 'Пауза способностей', 'icon': '⚡', 'type': 'float', 'source': 'timing',
        'description': 'Пауза при прожатии способности героя.', 'min': 0.0, 'max': 10.0,
    },
    'HERO_ABILITY_DELAY_4': {
        'category': 'attack', 'label': 'Задержка героя 4', 'icon': '4️⃣', 'type': 'float', 'source': 'hero_delay', 'hero_key': '4',
        'description': 'Через сколько секунд прожимать способность героя 4 после высадки.', 'min': 0.0, 'max': 60.0,
    },
    'HERO_ABILITY_DELAY_5': {
        'category': 'attack', 'label': 'Задержка героя 5', 'icon': '5️⃣', 'type': 'float', 'source': 'hero_delay', 'hero_key': '5',
        'description': 'Через сколько секунд прожимать способность героя 5 после высадки.', 'min': 0.0, 'max': 60.0,
    },
    'HERO_ABILITY_DELAY_6': {
        'category': 'attack', 'label': 'Задержка героя 6', 'icon': '6️⃣', 'type': 'float', 'source': 'hero_delay', 'hero_key': '6',
        'description': 'Через сколько секунд прожимать способность героя 6 после высадки.', 'min': 0.0, 'max': 60.0,
    },
    'HERO_ABILITY_DELAY_7': {
        'category': 'attack', 'label': 'Задержка героя 7', 'icon': '7️⃣', 'type': 'float', 'source': 'hero_delay', 'hero_key': '7',
        'description': 'Через сколько секунд прожимать способность героя 7 после высадки.', 'min': 0.0, 'max': 60.0,
    },
    'BATTLE_MACHINE_DEPLOY_SLEEP': {
        'category': 'attack', 'label': 'Пауза машины', 'icon': '🛠️', 'type': 'float', 'source': 'timing',
        'description': 'Пауза при высадке осадной машины.', 'min': 0.0, 'max': 10.0,
    },
    'SPELL_SELECT_SLEEP': {
        'category': 'attack', 'label': 'Пауза выбора спелла', 'icon': '🪄', 'type': 'float', 'source': 'timing',
        'description': 'Пауза после выбора слота спеллов.', 'min': 0.0, 'max': 10.0,
    },
    'SURRENDER_WAIT': {
        'category': 'attack', 'label': 'Сдаться через', 'icon': '🏳️', 'type': 'float', 'source': 'timing',
        'description': 'Сколько секунд ждать до выхода из боя.', 'min': 0.0, 'max': 180.0,
    },
    'ENABLE_BATTLE_GOLD_FILTER': {
        'category': 'loot', 'label': 'Фильтр лута', 'icon': '✅', 'type': 'bool', 'source': 'config',
        'description': 'Если выключить, бот перестанет отсеивать слабые базы по золоту и эликсиру.',
    },
    'BATTLE_GOLD_MIN': {
        'category': 'loot', 'label': 'Мин. золото', 'icon': '🪙', 'type': 'int', 'source': 'config',
        'description': 'Минимум золота в бою для начала атаки.', 'min': 0, 'max': 10000000,
    },
    'BATTLE_GOLD_REGION': {
        'category': 'loot', 'label': 'OCR регион золота', 'icon': '📐', 'type': 'region', 'source': 'config',
        'description': 'Регион OCR золота в бою. Формат: x,y,w,h',
    },
    'BATTLE_ELIXIR_MIN': {
        'category': 'loot', 'label': 'Мин. эликсир', 'icon': '🧪', 'type': 'int', 'source': 'config',
        'description': 'Минимум эликсира в бою для начала атаки.', 'min': 0, 'max': 10000000,
    },
    'BATTLE_ELIXIR_REGION': {
        'category': 'loot', 'label': 'OCR регион эликсира', 'icon': '📏', 'type': 'region', 'source': 'config',
        'description': 'Регион OCR эликсира в бою. Формат: x,y,w,h',
    },
    'BATTLE_GOLD_REROLL_SLEEP': {
        'category': 'loot', 'label': 'Пауза reroll', 'icon': '🔁', 'type': 'float', 'source': 'config',
        'description': 'Пауза после Enter при пропуске базы.', 'min': 0.0, 'max': 10.0,
    },
    'BATTLE_GOLD_OCR_MAX_REROLLS': {
        'category': 'loot', 'label': 'Макс. reroll', 'icon': '♻️', 'type': 'int', 'source': 'config',
        'description': 'Максимум попыток reroll подряд.', 'min': 1, 'max': 10000,
    },
    'BATTLE_GOLD_ACCEPT_ON_UNKNOWN': {
        'category': 'loot', 'label': 'Атаковать при n/a', 'icon': '❓', 'type': 'bool', 'source': 'config',
        'description': 'Если включено, при неудачном OCR бот оставит текущую базу.',
    },
    'BATTLE_GOLD_UNRELIABLE_BELOW': {
        'category': 'loot', 'label': 'Порог недоверия OCR', 'icon': '📉', 'type': 'int', 'source': 'config',
        'description': 'Если OCR прочитал слишком маленькое число, база не будет скипнута автоматически.', 'min': 0, 'max': 1000000,
    },
    'BATTLE_RESOURCE_DEBUG_LOG': {
        'category': 'loot', 'label': 'Debug OCR', 'icon': '🧾', 'type': 'bool', 'source': 'config',
        'description': 'Писать подробные логи OCR в консоль и Telegram console mode.',
    },
    'SPELL_MODE': {
        'category': 'spells', 'label': 'Режим спеллов', 'icon': '🎛️', 'type': 'enum', 'source': 'spell_mode',
        'description': 'Переключение между текущими режимами спеллов.', 'choices': ('stoneDick', 'crazyWalls'),
    },
    'SPELL_COUNT': {
        'category': 'spells', 'label': 'Число спеллов', 'icon': '✨', 'type': 'int', 'source': 'config',
        'description': 'Сколько спеллов выбрасывать за атаку.', 'min': 1, 'max': 50,
    },
    'SPELL_INTERVAL': {
        'category': 'spells', 'label': 'Интервал спеллов', 'icon': '⏳', 'type': 'float', 'source': 'timing',
        'description': 'Интервал между кастами спеллов в обычном режиме.', 'min': 0.0, 'max': 10.0,
    },
    'SPELL_POINT_JITTER_X_PX': {
        'category': 'spells', 'label': 'Jitter X', 'icon': '↔️', 'type': 'int', 'source': 'config',
        'description': 'Горизонтальный разброс точек для режима stoneDick.', 'min': 0, 'max': 500,
    },
    'SPELL_POINT_JITTER_Y_PX': {
        'category': 'spells', 'label': 'Jitter Y', 'icon': '↕️', 'type': 'int', 'source': 'config',
        'description': 'Вертикальный разброс точек для режима stoneDick.', 'min': 0, 'max': 500,
    },
    'SPELL_CRAZYWALLS_OFFSET_PX': {
        'category': 'spells', 'label': 'CrazyWalls offset', 'icon': '🧱', 'type': 'int', 'source': 'config',
        'description': 'Размер квадрата для режима crazyWalls.', 'min': 1, 'max': 500,
    },
    'SPELL_CRAZYWALLS_TOTAL_SECONDS': {
        'category': 'spells', 'label': 'CrazyWalls длительность', 'icon': '⚡', 'type': 'float', 'source': 'config',
        'description': 'Общая длительность раскидки спеллов в режиме crazyWalls.', 'min': 0.1, 'max': 20.0,
    },
    'SEARCH_WAIT_SPACE': {
        'category': 'attack', 'label': 'Поиск: пауза Space', 'icon': '🔎', 'type': 'float', 'source': 'search_sequence', 'search_index': 0,
        'description': 'Пауза после Space в цепочке старта поиска базы.', 'min': 0.0, 'max': 10.0,
    },
    'SEARCH_WAIT_E': {
        'category': 'attack', 'label': 'Поиск: пауза E', 'icon': '🔍', 'type': 'float', 'source': 'search_sequence', 'search_index': 1,
        'description': 'Пауза после E в цепочке старта поиска базы.', 'min': 0.0, 'max': 10.0,
    },
    'SEARCH_WAIT_I': {
        'category': 'attack', 'label': 'Поиск: пауза I', 'icon': '🎯', 'type': 'float', 'source': 'search_sequence', 'search_index': 2,
        'description': 'Пауза после I в цепочке старта поиска базы.', 'min': 0.0, 'max': 10.0,
    },
    'WALL_KEY_CYCLE_ENABLED': {
        'category': 'wall', 'label': 'Проходка стен', 'icon': '🧱', 'type': 'bool', 'source': 'wall_enabled',
        'description': 'Включает или выключает запуск wall macro по счетчику атак.',
    },
    'WALL_KEY_CYCLE_EVERY_ATTACKS': {
        'category': 'wall', 'label': 'После скольких боев', 'icon': '🔢', 'type': 'int', 'source': 'wall_every',
        'description': 'Через сколько атак запускать wall macro.', 'min': 1, 'max': 10000,
    },
    'WALL_KEY_CYCLE_DURATION_SECONDS': {
        'category': 'wall', 'label': 'Длительность проходки', 'icon': '⌛', 'type': 'float', 'source': 'config',
        'description': 'Сколько секунд ждать после нажатия wall hotkey.', 'min': 0.0, 'max': 600.0,
    },
    'ENABLE_STORAGE_MONITOR': {
        'category': 'storage', 'label': 'Монитор хранилищ', 'icon': '🏦', 'type': 'bool', 'source': 'config',
        'description': 'Если включено, бот периодически проверяет заполненность хранилищ.',
    },
    'STORAGE_MONITOR_EVERY_ATTACKS': {
        'category': 'storage', 'label': 'Проверка каждые', 'icon': '🔁', 'type': 'int', 'source': 'config',
        'description': 'Через сколько атак проверять хранилища.', 'min': 1, 'max': 10000,
    },
    'STORAGE_MONITOR_THRESHOLD': {
        'category': 'storage', 'label': 'Порог хранилищ', 'icon': '📦', 'type': 'int', 'source': 'config',
        'description': 'Если золото и эликсир выше этого порога, бот остановится.', 'min': 0, 'max': 100000000,
    },
    'STORAGE_MONITOR_GOLD_REGION': {
        'category': 'storage', 'label': 'Регион хранилища золота', 'icon': '🪙', 'type': 'region', 'source': 'config',
        'description': 'Регион OCR общего золота в хранилище. Формат: x,y,w,h',
    },
    'STORAGE_MONITOR_ELIXIR_REGION': {
        'category': 'storage', 'label': 'Регион хранилища эликсира', 'icon': '🧪', 'type': 'region', 'source': 'config',
        'description': 'Регион OCR общего эликсира в хранилище. Формат: x,y,w,h',
    },
    'BATTLE_REPORT_EVERY': {
        'category': 'storage', 'label': 'Скрины боев', 'icon': '📸', 'type': 'int', 'source': 'battle_report_every',
        'description': 'Каждые N боев отправлять скрин. 0 = выключено.', 'min': 0, 'max': 10000,
    },
    'ENABLE_AUTO_RECOVERY': {
        'category': 'recovery', 'label': 'Автовосстановление', 'icon': '🛟', 'type': 'bool', 'source': 'config',
        'description': 'Включает watchdog и попытки восстановления.',
    },
    'RECOVERY_MAX_LOOP_SECONDS': {
        'category': 'recovery', 'label': 'Макс. время цикла', 'icon': '⏲️', 'type': 'float', 'source': 'config',
        'description': 'Если цикл длится слишком долго, recovery сочтет это зависанием.', 'min': 10.0, 'max': 3600.0,
    },
    'RECOVERY_NO_PROGRESS_SECONDS': {
        'category': 'recovery', 'label': 'Нет прогресса', 'icon': '🧊', 'type': 'float', 'source': 'config',
        'description': 'Через сколько секунд без progress heartbeat включать recovery.', 'min': 10.0, 'max': 3600.0,
    },
    'RECOVERY_STALE_SCREEN_SECONDS': {
        'category': 'recovery', 'label': 'Застывший экран', 'icon': '🖼️', 'type': 'float', 'source': 'config',
        'description': 'Через сколько секунд неизменный экран считать зависшим.', 'min': 10.0, 'max': 3600.0,
    },
    'RECOVERY_BLACK_SCREEN_BRIGHTNESS_MAX': {
        'category': 'recovery', 'label': 'Черный экран: яркость', 'icon': '🌑', 'type': 'float', 'source': 'config',
        'description': 'Максимальная яркость для детекта почти черного экрана.', 'min': 0.0, 'max': 255.0,
    },
    'RECOVERY_BLACK_SCREEN_MIN_COVERAGE': {
        'category': 'recovery', 'label': 'Черный экран: покрытие', 'icon': '📐', 'type': 'float', 'source': 'config',
        'description': 'Какую долю экрана должна занимать темнота, чтобы сработал black-screen recovery.', 'min': 0.0, 'max': 1.0,
    },
    'RECOVERY_ERROR_CONFIDENCE': {
        'category': 'recovery', 'label': 'Confidence ошибок', 'icon': '🚨', 'type': 'float', 'source': 'config',
        'description': 'Порог совпадения шаблонов из папки errors.', 'min': 0.1, 'max': 1.0,
    },
    'RECOVERY_STALE_SAMPLE_INTERVAL_SECONDS': {
        'category': 'recovery', 'label': 'Интервал stale-check', 'icon': '🕒', 'type': 'float', 'source': 'config',
        'description': 'Как часто проверять, что экран застрял.', 'min': 0.5, 'max': 60.0,
    },
    'RECOVERY_RATE_WINDOW_SECONDS': {
        'category': 'recovery', 'label': 'Окно recovery', 'icon': '🪟', 'type': 'float', 'source': 'config',
        'description': 'Окно времени для лимита аварийных рестартов.', 'min': 60.0, 'max': 86400.0,
    },
    'RECOVERY_MAX_ATTEMPTS_PER_WINDOW': {
        'category': 'recovery', 'label': 'Лимит recovery', 'icon': '🧯', 'type': 'int', 'source': 'config',
        'description': 'Сколько recovery-действий разрешено в одном окне времени.', 'min': 1, 'max': 100,
    },
    'IMAGE_MATCH_CONFIDENCE': {
        'category': 'screen', 'label': 'Confidence поиска', 'icon': '🧠', 'type': 'float', 'source': 'config',
        'description': 'Общий порог совпадения картинок на экране.', 'min': 0.1, 'max': 1.0,
    },
    'WAIT_FOR_IMAGE_TIMEOUT_SECONDS': {
        'category': 'screen', 'label': 'Таймаут ожидания', 'icon': '⌛', 'type': 'float', 'source': 'config',
        'description': 'Общий таймаут ожидания screen guards.', 'min': 1.0, 'max': 3600.0,
    },
    'SEARCH_BUTTON_CHECK_INTERVAL_SECONDS': {
        'category': 'screen', 'label': 'Проверка home', 'icon': '🏠', 'type': 'float', 'source': 'config',
        'description': 'Как часто искать домашний экран.', 'min': 0.1, 'max': 60.0,
    },
    'ARMY_READY_CHECK_INTERVAL_SECONDS': {
        'category': 'screen', 'label': 'Проверка battle', 'icon': '⚔️', 'type': 'float', 'source': 'config',
        'description': 'Как часто искать battle-ready экран.', 'min': 0.1, 'max': 60.0,
    },
    'GO_HOME_CHECK_INTERVAL_SECONDS': {
        'category': 'screen', 'label': 'Проверка go home', 'icon': '🏡', 'type': 'float', 'source': 'config',
        'description': 'Как часто искать кнопку возврата домой.', 'min': 0.1, 'max': 60.0,
    },
}

CATEGORY_ORDER = ['attack', 'loot', 'spells', 'wall', 'storage', 'recovery', 'screen']


def category_ids():
    return list(CATEGORY_ORDER)


def category_meta(category_id):
    return CATEGORY_META[category_id]


def settings_for_category(category_id):
    return [key for key, meta in SETTINGS.items() if meta['category'] == category_id]


def get_setting_meta(setting_id):
    return SETTINGS[setting_id]


def _format_int(value):
    return f'{int(value):,}'.replace(',', ' ')


def _format_float(value):
    text = f'{float(value):.2f}'.rstrip('0').rstrip('.')
    return f'{text}с'


def _format_region(value):
    if value is None:
        return 'off'
    if isinstance(value, (list, tuple)) and len(value) == 4:
        return ', '.join(str(int(item)) for item in value)
    return str(value)


def get_setting_value(setting_id):
    meta = get_setting_meta(setting_id)
    source = meta['source']
    if source == 'config':
        return live_config.get(meta.get('key', setting_id), getattr(cfg, meta.get('key', setting_id), None))
    if source == 'timing':
        return runtime_state.get_timing_override(setting_id, default=getattr(cfg, setting_id))
    if source == 'hero_delay':
        defaults = getattr(cfg, 'HERO_ABILITY_DELAY_BY_KEY', {})
        return live_config.get_hero_ability_delay(meta['hero_key'], defaults.get(meta['hero_key'], 0.0))
    if source == 'wall_enabled':
        return runtime_state.wall_key_cycle_enabled(default=bool(getattr(cfg, 'ENABLE_WALL_KEY_CYCLE', True)))
    if source == 'wall_every':
        return runtime_state.get_wall_key_cycle_every_override(default=int(getattr(cfg, 'WALL_KEY_CYCLE_EVERY_ATTACKS', 20)))
    if source == 'battle_report_every':
        return runtime_state.get_battle_report_every_override(default=int(getattr(cfg, 'BATTLE_REPORT_EVERY', 0)))
    if source == 'spell_mode':
        return runtime_state.get_spell_mode(default=getattr(cfg, 'SPELL_MODE_DEFAULT', 'stoneDick'))
    if source == 'search_sequence':
        sequence = getattr(cfg, 'SEARCH_SEQUENCE', [])
        index = int(meta.get('search_index', 0))
        default = 0.0
        if 0 <= index < len(sequence):
            try:
                default = float(sequence[index][1])
            except (TypeError, ValueError, IndexError):
                default = 0.0
        return live_config.get_float(setting_id, default)
    return None


def format_setting_value(setting_id, value=None):
    meta = get_setting_meta(setting_id)
    if value is None:
        value = get_setting_value(setting_id)
    kind = meta['type']
    if kind == 'bool':
        return '✅' if bool(value) else '❌'
    if kind == 'int':
        return _format_int(int(value))
    if kind == 'float':
        return _format_float(float(value))
    if kind == 'region':
        return _format_region(value)
    if kind == 'enum' and setting_id == 'SPELL_MODE':
        return spell_mode_label(value)
    return str(value)


def build_setting_button_text(setting_id):
    meta = get_setting_meta(setting_id)
    return f"{meta['icon']} {meta['label']}: {format_setting_value(setting_id)}"


def build_setting_prompt_text(setting_id):
    meta = get_setting_meta(setting_id)
    current = format_setting_value(setting_id)
    suffix = ''
    if meta['type'] == 'bool':
        suffix = 'Нажми кнопку еще раз, чтобы переключить значение.'
    elif meta['type'] == 'enum':
        suffix = 'Нажми кнопку еще раз, чтобы переключить режим.'
    elif meta['type'] == 'region':
        suffix = 'Введи 4 числа через запятую: x,y,w,h. Пример: 35,190,170,45'
    else:
        suffix = 'Введи новое значение сообщением.'
    return (
        f"{meta['icon']} {meta['label']}\n"
        "────────────\n"
        f"Текущее: {current}\n"
        f"{meta['description']}\n"
        f"{suffix}"
    )


def toggle_setting(setting_id):
    meta = get_setting_meta(setting_id)
    if meta['type'] == 'enum' and setting_id == 'SPELL_MODE':
        current = str(get_setting_value(setting_id))
        next_value = 'crazyWalls' if current == 'stoneDick' else 'stoneDick'
        runtime_state.set_spell_mode(next_value)
        return next_value
    current = bool(get_setting_value(setting_id))
    next_value = not current
    source = meta['source']
    if source == 'config':
        runtime_state.set_config_override(meta.get('key', setting_id), next_value)
    elif source == 'wall_enabled':
        runtime_state.set_wall_key_cycle_enabled(next_value)
    else:
        raise ValueError(f'toggle unsupported for source: {source}')
    return next_value


def _parse_bool(raw_text):
    text = str(raw_text or '').strip().lower()
    if text in ('1', 'true', 'on', 'yes', 'да', 'вкл', 'enable', 'enabled'):
        return True
    if text in ('0', 'false', 'off', 'no', 'нет', 'выкл', 'disable', 'disabled'):
        return False
    raise ValueError('bad bool')


def set_setting_value(setting_id, raw_text):
    meta = get_setting_meta(setting_id)
    kind = meta['type']
    text = str(raw_text or '').strip().replace(',', '.')
    if kind == 'bool':
        parsed = _parse_bool(text)
    elif kind == 'int':
        parsed = int(float(text))
    elif kind == 'float':
        parsed = float(text)
    elif kind == 'enum':
        raw = str(raw_text or '').strip().lower()
        choices = tuple(str(item).strip() for item in meta.get('choices', ()))
        normalized = None
        for item in choices:
            if raw == item.lower():
                normalized = item
                break
        if normalized is None:
            raise ValueError('bad enum')
        parsed = normalized
    elif kind == 'region':
        raw = str(raw_text or '').strip()
        if raw.lower() in ('off', 'none', 'null'):
            parsed = None
        else:
            parts = [part.strip() for part in raw.split(',')]
            if len(parts) != 4:
                raise ValueError('bad region')
            parsed = tuple(int(float(part)) for part in parts)
    else:
        parsed = raw_text

    if kind != 'region' and 'min' in meta and parsed < meta['min']:
        raise ValueError('below min')
    if kind != 'region' and 'max' in meta and parsed > meta['max']:
        raise ValueError('above max')

    source = meta['source']
    if source == 'config':
        runtime_state.set_config_override(meta.get('key', setting_id), parsed)
    elif source == 'timing':
        runtime_state.set_timing_override(setting_id, parsed)
    elif source == 'hero_delay':
        runtime_state.set_config_override(f"HERO_ABILITY_DELAY_{meta['hero_key']}", parsed)
    elif source == 'wall_enabled':
        runtime_state.set_wall_key_cycle_enabled(bool(parsed))
    elif source == 'wall_every':
        runtime_state.set_wall_key_cycle_every_override(int(parsed))
    elif source == 'battle_report_every':
        runtime_state.set_battle_report_every_override(int(parsed))
    elif source == 'spell_mode':
        runtime_state.set_spell_mode(parsed)
    elif source == 'search_sequence':
        runtime_state.set_config_override(setting_id, parsed)
    else:
        raise ValueError(f'unsupported source: {source}')
    return parsed
