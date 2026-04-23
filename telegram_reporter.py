import io
import json
import threading
import time
import uuid
import urllib.parse
import urllib.request

import config as cfg
import runtime_state

def _to_image_bytes(image):
    image_format = getattr(cfg, 'BATTLE_SCREENSHOT_FORMAT', 'JPEG').upper()
    if image_format == 'JPEG':
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        buffer = io.BytesIO()
        image.save(
            buffer,
            format='JPEG',
            quality=getattr(cfg, 'BATTLE_SCREENSHOT_JPEG_QUALITY', 85),
        )
        return buffer.getvalue(), 'image/jpeg', 'jpg'

    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue(), 'image/png', 'png'

def save_screenshot_local(image, cycle_number=None):
    if not getattr(cfg, 'SAVE_BATTLE_SCREENSHOTS_LOCAL', False):
        return None

    import os

    directory = getattr(cfg, 'BATTLE_SCREENSHOT_DIR', 'screenshots')
    os.makedirs(directory, exist_ok=True)
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    suffix = f'_cycle_{cycle_number}' if cycle_number is not None else ''
    image_format = getattr(cfg, 'BATTLE_SCREENSHOT_FORMAT', 'JPEG').lower()
    ext = 'jpg' if image_format == 'jpeg' else image_format
    path = os.path.join(directory, f'battle_{timestamp}{suffix}.{ext}')
    image.save(path, format=image_format.upper())
    return path

def _build_multipart_payload(fields, file_field_name, filename, file_bytes, mime_type):
    boundary = f'----CodexBoundary{uuid.uuid4().hex}'
    body = bytearray()

    for key, value in fields.items():
        body.extend(f'--{boundary}\r\n'.encode())
        body.extend(
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
        )
        body.extend(str(value).encode('utf-8'))
        body.extend(b'\r\n')

    body.extend(f'--{boundary}\r\n'.encode())
    body.extend(
        (
            f'Content-Disposition: form-data; name="{file_field_name}"; '
            f'filename="{filename}"\r\n'
        ).encode()
    )
    body.extend(f'Content-Type: {mime_type}\r\n\r\n'.encode())
    body.extend(file_bytes)
    body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode())
    return bytes(body), boundary

def send_battle_screenshot(image, cycle_number=None, caption_prefix='Clash of Clans battle result'):
    if not getattr(cfg, 'ENABLE_TELEGRAM_REPORTS', False):
        return False

    token = getattr(cfg, 'TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = str(getattr(cfg, 'TELEGRAM_CHAT_ID', '')).strip()
    if not token or not chat_id:
        print('Telegram disabled: missing token/chat id.')
        return False

    try:
        file_bytes, mime_type, ext = _to_image_bytes(image)
    except Exception as exc:
        print(f'Telegram screenshot encode failed: {exc}')
        return False

    cycle_label = f' #{cycle_number}' if cycle_number is not None else ''
    caption = f'{caption_prefix}{cycle_label}'
    payload, boundary = _build_multipart_payload(
        {
            'chat_id': chat_id,
            'caption': caption,
        },
        'photo',
        f'battle_result.{ext}',
        file_bytes,
        mime_type,
    )

    request = urllib.request.Request(
        f'https://api.telegram.org/bot{token}/sendPhoto',
        data=payload,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
        },
        method='POST',
    )

    timeout = getattr(cfg, 'TELEGRAM_SEND_TIMEOUT_SECONDS', 10)
    retries = max(0, int(getattr(cfg, 'TELEGRAM_SEND_RETRIES', 1)))

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode('utf-8')
            parsed = json.loads(raw)
            if parsed.get('ok'):
                message_id = (
                    parsed.get('result', {})
                    .get('message_id')
                )
                if message_id is not None:
                    runtime_state.add_telegram_battle_screenshot_message_id(message_id)
            return True
        except Exception as exc:
            if attempt >= retries:
                print(f'Telegram send failed: {exc}')
                return False
            time.sleep(1)

    return False

def send_text_message(text):
    token = getattr(cfg, 'TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = str(getattr(cfg, 'TELEGRAM_CHAT_ID', '')).strip()
    if not token or not chat_id:
        return False

    timeout = getattr(cfg, 'TELEGRAM_SEND_TIMEOUT_SECONDS', 10)
    retries = max(0, int(getattr(cfg, 'TELEGRAM_SEND_RETRIES', 1)))
    payload = urllib.parse.urlencode(
        {
            'chat_id': chat_id,
            'text': str(text),
        }
    ).encode('utf-8')
    request = urllib.request.Request(
        f'https://api.telegram.org/bot{token}/sendMessage',
        data=payload,
        method='POST',
    )

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode('utf-8')
            parsed = json.loads(raw)
            if parsed.get('ok'):
                delete_after = int(getattr(cfg, 'RECOVERY_TELEGRAM_DELETE_AFTER_SECONDS', 0) or 0)
                message_id = parsed.get('result', {}).get('message_id')
                if delete_after > 0 and message_id is not None:
                    threading.Thread(
                        target=_delete_message_later,
                        args=(token, chat_id, int(message_id), delete_after),
                        daemon=True,
                    ).start()
                return True
            return False
        except Exception as exc:
            if attempt >= retries:
                print(f'Telegram send text failed: {exc}')
                return False
            time.sleep(1)
    return False


def _delete_message_later(token, chat_id, message_id, delay_seconds):
    try:
        time.sleep(max(0, int(delay_seconds)))
        payload = urllib.parse.urlencode(
            {
                'chat_id': str(chat_id),
                'message_id': int(message_id),
            }
        ).encode('utf-8')
        request = urllib.request.Request(
            f'https://api.telegram.org/bot{token}/deleteMessage',
            data=payload,
            method='POST',
        )
        urllib.request.urlopen(request, timeout=getattr(cfg, 'TELEGRAM_SEND_TIMEOUT_SECONDS', 10)).read()
    except Exception:
        return

def upsert_attack_log_message(text):
    token = getattr(cfg, 'TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = str(getattr(cfg, 'TELEGRAM_CHAT_ID', '')).strip()
    if not token or not chat_id:
        return None

    timeout = getattr(cfg, 'TELEGRAM_SEND_TIMEOUT_SECONDS', 10)
    retries = max(0, int(getattr(cfg, 'TELEGRAM_SEND_RETRIES', 1)))
    message_id = runtime_state.get_telegram_attack_log_message_id()

    if message_id is not None:
        payload = urllib.parse.urlencode(
            {
                'chat_id': chat_id,
                'message_id': int(message_id),
                'text': str(text),
            }
        ).encode('utf-8')
        request = urllib.request.Request(
            f'https://api.telegram.org/bot{token}/editMessageText',
            data=payload,
            method='POST',
        )
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    raw = response.read().decode('utf-8')
                parsed = json.loads(raw)
                if parsed.get('ok'):
                    return message_id
                break
            except Exception:
                if attempt >= retries:
                    break
                time.sleep(1)

    payload = urllib.parse.urlencode(
        {
            'chat_id': chat_id,
            'text': str(text),
        }
    ).encode('utf-8')
    request = urllib.request.Request(
        f'https://api.telegram.org/bot{token}/sendMessage',
        data=payload,
        method='POST',
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode('utf-8')
            parsed = json.loads(raw)
            if parsed.get('ok'):
                new_message_id = parsed.get('result', {}).get('message_id')
                if new_message_id is not None:
                    runtime_state.set_telegram_attack_log_message_id(new_message_id)
                    return int(new_message_id)
            return None
        except Exception as exc:
            if attempt >= retries:
                print(f'Telegram send attack log failed: {exc}')
                return None
            time.sleep(1)

    return None

def upsert_console_log_message():
    if not runtime_state.telegram_console_enabled(default=False):
        return None

    token = getattr(cfg, 'TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = str(getattr(cfg, 'TELEGRAM_CHAT_ID', '')).strip()
    if not token or not chat_id:
        return None

    lines = runtime_state.get_telegram_console_lines()
    if not lines:
        text = '🖥️ Console mode\n────────────\nПока нет событий.'
    else:
        text = '🖥️ Console mode\n────────────\n' + '\n'.join(lines)

    timeout = getattr(cfg, 'TELEGRAM_SEND_TIMEOUT_SECONDS', 10)
    retries = max(0, int(getattr(cfg, 'TELEGRAM_SEND_RETRIES', 1)))
    message_id = runtime_state.get_telegram_console_message_id()

    if message_id is not None:
        payload = urllib.parse.urlencode(
            {
                'chat_id': chat_id,
                'message_id': int(message_id),
                'text': text,
            }
        ).encode('utf-8')
        request = urllib.request.Request(
            f'https://api.telegram.org/bot{token}/editMessageText',
            data=payload,
            method='POST',
        )
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    raw = response.read().decode('utf-8')
                parsed = json.loads(raw)
                if parsed.get('ok'):
                    return message_id
                break
            except Exception as exc:
                if 'message is not modified' in str(exc).lower():
                    return message_id
                if attempt >= retries:
                    break
                time.sleep(1)

    payload = urllib.parse.urlencode({'chat_id': chat_id, 'text': text}).encode('utf-8')
    request = urllib.request.Request(
        f'https://api.telegram.org/bot{token}/sendMessage',
        data=payload,
        method='POST',
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode('utf-8')
            parsed = json.loads(raw)
            if parsed.get('ok'):
                new_message_id = parsed.get('result', {}).get('message_id')
                if new_message_id is not None:
                    runtime_state.set_telegram_console_message_id(new_message_id)
                    return int(new_message_id)
            return None
        except Exception as exc:
            if attempt >= retries:
                print(f'Telegram send console log failed: {exc}')
                return None
            time.sleep(1)
    return None

def append_console_log(text):
    if not runtime_state.telegram_console_enabled(default=False):
        return None
    runtime_state.append_telegram_console_line(text)
    return upsert_console_log_message()
