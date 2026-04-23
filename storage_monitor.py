import config as cfg
import gold_filter
import live_config as lcfg
import telegram_reporter


def read_storage_totals():
    gold = gold_filter.read_numeric_region(
        region=lcfg.get_region('STORAGE_MONITOR_GOLD_REGION', getattr(cfg, 'STORAGE_MONITOR_GOLD_REGION', (1145, 104, 316, 47))),
        min_value=lcfg.get_int('STORAGE_MONITOR_THRESHOLD', 29000000),
        inner_crop=getattr(cfg, 'STORAGE_MONITOR_GOLD_INNER_CROP', (18, 2, 10, 2)),
    )
    elixir = gold_filter.read_numeric_region(
        region=lcfg.get_region('STORAGE_MONITOR_ELIXIR_REGION', getattr(cfg, 'STORAGE_MONITOR_ELIXIR_REGION', (1145, 180, 313, 48))),
        min_value=lcfg.get_int('STORAGE_MONITOR_THRESHOLD', 29000000),
        inner_crop=getattr(cfg, 'STORAGE_MONITOR_ELIXIR_INNER_CROP', (18, 2, 10, 2)),
    )
    return {'gold': gold, 'elixir': elixir}


def storages_are_full():
    payload = read_storage_totals()
    threshold = lcfg.get_int('STORAGE_MONITOR_THRESHOLD', 29000000)
    gold_value = payload.get('gold', {}).get('value')
    elixir_value = payload.get('elixir', {}).get('value')
    full = gold_value is not None and elixir_value is not None and gold_value > threshold and elixir_value > threshold

    if lcfg.get_bool('BATTLE_RESOURCE_DEBUG_LOG', True):
        text = (
            'Storage scan: '
            f'gold={gold_value if gold_value is not None else "n/a"} '
            f'candidates={gold_filter._fmt_candidates(payload.get("gold", {}).get("candidates", []))} '
            f'raw={gold_filter._fmt_raw(payload.get("gold", {}).get("raw", []))}; '
            f'elixir={elixir_value if elixir_value is not None else "n/a"} '
            f'candidates={gold_filter._fmt_candidates(payload.get("elixir", {}).get("candidates", []))} '
            f'raw={gold_filter._fmt_raw(payload.get("elixir", {}).get("raw", []))}'
        )
        print(text)
        telegram_reporter.append_console_log(text)

    payload['full'] = full
    return payload


def notify_full_storages(payload):
    gold_value = payload.get('gold', {}).get('value')
    elixir_value = payload.get('elixir', {}).get('value')
    text = (
        '🏦 Хранилища заполнены\n'
        f'🪙 Золото: {gold_value if gold_value is not None else "n/a"}\n'
        f'🧪 Эликсир: {elixir_value if elixir_value is not None else "n/a"}\n'
        '⛔ Бот остановлен.'
    )
    telegram_reporter.send_text_message(text)
    telegram_reporter.append_console_log('Storages full detected. Bot stopped.')
