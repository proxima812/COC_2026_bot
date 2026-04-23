import os
import re
import subprocess
import tempfile
import time
import uuid
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import pyautogui

import config as cfg
import live_config as lcfg
import telegram_reporter

_OCR_WHITELIST = '0123456789$SsOoBbIl|,. '
_OCR_REPLACE_MAP = str.maketrans(
    {
        '$': '5',
        'S': '5',
        's': '5',
        'O': '0',
        'o': '0',
        'B': '8',
        'I': '1',
        'l': '1',
        '|': '1',
    }
)
_DIGIT_CANVAS = (36, 24)


def _normalize_ocr_text(raw_text):
    text = str(raw_text or '').translate(_OCR_REPLACE_MAP)
    text = re.sub(r'[^0-9]', '', text)
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _extract_grouped_values(raw_text):
    text = str(raw_text or '').translate(_OCR_REPLACE_MAP)
    values = []
    for token in re.findall(r'\d{1,3}(?:[ ,.\u202f]\d{3})+', text):
        compact = re.sub(r'[^0-9]', '', token)
        if not compact:
            continue
        try:
            values.append(int(compact))
        except ValueError:
            pass
    return values


def _extract_values_from_ocr_text(raw_text):
    text = str(raw_text or '').translate(_OCR_REPLACE_MAP)
    values = list(_extract_grouped_values(text))

    for token in re.findall(r'[0-9$SsOoBbIl|]{4,}', text):
        value = _normalize_ocr_text(token)
        if value is not None:
            values.append(value)

    split_chunks = re.findall(r'[0-9$SsOoBbIl|]+', text)
    if len(split_chunks) >= 2:
        merged = ''.join(chunk.translate(_OCR_REPLACE_MAP) for chunk in split_chunks)
        merged = re.sub(r'[^0-9]', '', merged)
        if merged:
            try:
                values.append(int(merged))
            except ValueError:
                pass

    if not values:
        value = _normalize_ocr_text(text)
        if value is not None:
            values.append(value)
    return values


def _clean_raw_ocr_text(raw_text):
    text = str(raw_text or '').translate(_OCR_REPLACE_MAP)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _select_stable_gold_value(values):
    if not values:
        return None

    max_gold = max(1000, int(getattr(cfg, 'BATTLE_GOLD_MAX', 3000000)))
    filtered = [value for value in values if 0 < value <= max_gold]
    if not filtered:
        return None

    min_gold = max(1, int(getattr(cfg, 'BATTLE_GOLD_MIN', 450000)))
    min_digits = int(getattr(cfg, 'BATTLE_GOLD_TEMPLATE_MIN_DIGITS', len(str(min_gold))))
    long_candidates = [value for value in filtered if len(str(value)) >= min_digits]
    if long_candidates:
        filtered = long_candidates

    counts = Counter(filtered)
    top_count = max(counts.values())
    top_values = sorted([value for value, count in counts.items() if count == top_count])
    if top_count >= 2:
        return top_values[0]

    return max(filtered)


def _resource_debug_dir():
    root = str(getattr(cfg, 'BATTLE_RESOURCE_DEBUG_DIR', 'debug/battle_loot')).strip()
    if not root:
        root = 'debug/battle_loot'
    if not os.path.isabs(root):
        root = os.path.join(os.path.dirname(__file__), root)
    os.makedirs(root, exist_ok=True)
    return root


def _save_bad_resource_read(image_rgb, resource_name, region, stage, raw_samples):
    if not bool(getattr(cfg, 'BATTLE_RESOURCE_DEBUG_SAVE_BAD_READS', False)):
        return
    try:
        root = _resource_debug_dir()
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        suffix = uuid.uuid4().hex[:8]
        image_path = os.path.join(root, f'{resource_name}_{timestamp}_{suffix}.png')
        meta_path = os.path.join(root, f'{resource_name}_{timestamp}_{suffix}.txt')
        cv2.imwrite(image_path, cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
        with open(meta_path, 'w', encoding='utf-8') as handle:
            handle.write(f'resource={resource_name}\n')
            handle.write(f'region={tuple(int(v) for v in region)}\n')
            handle.write(f'stage={stage}\n')
            handle.write(f'raw={list(raw_samples or [])}\n')
    except Exception:
        return


def _run_tesseract(image_path, psm):
    command = [
        'tesseract',
        image_path,
        'stdout',
        '--psm',
        str(int(psm)),
        '-c',
        f'tessedit_char_whitelist={_OCR_WHITELIST}',
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ''
    if completed.returncode != 0:
        return ''
    return completed.stdout.strip()


def _template_dir():
    root = str(getattr(cfg, 'BATTLE_GOLD_TEMPLATE_DIR', '.digit_templates/battle_gold')).strip()
    path = Path(root)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_digit_mask(mask):
    ys, xs = np.where(mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        return None
    x0, x1 = xs.min(), xs.max() + 1
    y0, y1 = ys.min(), ys.max() + 1
    cropped = mask[y0:y1, x0:x1]
    target_h, target_w = _DIGIT_CANVAS
    inner_h = max(1, target_h - 4)
    inner_w = max(1, target_w - 4)
    scale = min(inner_w / max(1, cropped.shape[1]), inner_h / max(1, cropped.shape[0]))
    resized = cv2.resize(
        cropped,
        (max(1, int(round(cropped.shape[1] * scale))), max(1, int(round(cropped.shape[0] * scale)))),
        interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC,
    )
    canvas = np.zeros((target_h, target_w), dtype=np.uint8)
    offset_y = (target_h - resized.shape[0]) // 2
    offset_x = (target_w - resized.shape[1]) // 2
    canvas[offset_y:offset_y + resized.shape[0], offset_x:offset_x + resized.shape[1]] = resized
    return canvas


def _digit_mask_variants(image_rgb):
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    scaled = cv2.resize(gray, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC)
    scaled_hsv = cv2.resize(hsv, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC)
    blur = cv2.GaussianBlur(scaled, (3, 3), 0)
    _, bright_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bright_fixed = cv2.inRange(blur, 145, 255)
    adaptive = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        -4,
    )
    white_mask = cv2.inRange(scaled_hsv, np.array([0, 0, 155], dtype=np.uint8), np.array([180, 90, 255], dtype=np.uint8))
    variants = []
    kernel = np.ones((2, 2), dtype=np.uint8)
    for base in (bright_otsu, bright_fixed, adaptive, white_mask):
        cleaned = cv2.morphologyEx(base, cv2.MORPH_OPEN, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
        variants.append(cleaned)
    return variants


def _segment_digit_masks(mask):
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    boxes = []
    height, width = mask.shape[:2]
    min_h = max(10, int(height * 0.38))
    min_w = max(5, int(width * 0.015))
    max_w = max(min_w + 1, int(width * 0.28))
    min_area = max(40, int(height * width * 0.002))

    for label in range(1, num_labels):
        x, y, w, h, area = stats[label]
        if h < min_h or w < min_w or w > max_w or area < min_area:
            continue
        if y > int(height * 0.72):
            continue
        boxes.append((x, y, w, h, area))

    if not boxes:
        return []

    heights = [box[3] for box in boxes]
    median_h = float(np.median(heights))
    filtered = [box for box in boxes if box[3] >= median_h * 0.72]
    filtered.sort(key=lambda item: item[0])

    glyphs = []
    for x, y, w, h, _ in filtered:
        digit = mask[max(0, y - 1):min(height, y + h + 1), max(0, x - 1):min(width, x + w + 1)]
        normalized = _normalize_digit_mask(digit)
        if normalized is not None:
            glyphs.append(normalized)
    return glyphs


def _choose_digit_glyphs(image_rgb):
    min_digits = int(getattr(cfg, 'BATTLE_GOLD_TEMPLATE_MIN_DIGITS', 6))
    max_digits = int(getattr(cfg, 'BATTLE_GOLD_TEMPLATE_MAX_DIGITS', 8))
    best = []
    best_score = (-1, -1)

    for mask in _digit_mask_variants(image_rgb):
        glyphs = _segment_digit_masks(mask)
        count = len(glyphs)
        if not glyphs:
            continue
        count_score = 2 if min_digits <= count <= max_digits else 1 if count >= 4 else 0
        area_score = int(sum(int(np.count_nonzero(glyph)) for glyph in glyphs))
        score = (count_score, area_score)
        if score > best_score:
            best = glyphs
            best_score = score
    return best


def _load_template_bank():
    root = _template_dir()
    bank = {}
    for digit in '0123456789':
        digit_dir = root / digit
        templates = []
        if digit_dir.exists():
            for image_path in sorted(digit_dir.glob('*.png')):
                template = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
                if template is None:
                    continue
                normalized = _normalize_digit_mask(template)
                if normalized is not None:
                    templates.append(normalized)
        bank[digit] = templates
    return bank


def _classify_digit(glyph, bank):
    best_digit = None
    best_score = -1.0
    glyph_f = glyph.astype(np.float32) / 255.0
    for digit, templates in bank.items():
        for template in templates:
            template_f = template.astype(np.float32) / 255.0
            diff_score = 1.0 - float(np.mean(np.abs(glyph_f - template_f)))
            corr = cv2.matchTemplate(glyph, template, cv2.TM_CCOEFF_NORMED)
            corr_score = float(corr[0][0]) if corr.size else 0.0
            score = max(diff_score, corr_score)
            if score > best_score:
                best_score = score
                best_digit = digit
    return best_digit, best_score


def _read_by_templates(image_rgb):
    glyphs = _choose_digit_glyphs(image_rgb)
    if not glyphs:
        return None, glyphs, None

    bank = _load_template_bank()
    threshold = float(getattr(cfg, 'BATTLE_GOLD_TEMPLATE_SCORE_THRESHOLD', 0.62))
    digits = []
    scores = []
    for glyph in glyphs:
        digit, score = _classify_digit(glyph, bank)
        if digit is None or score < threshold:
            return None, glyphs, score
        digits.append(digit)
        scores.append(score)

    min_digits = int(getattr(cfg, 'BATTLE_GOLD_TEMPLATE_MIN_DIGITS', 6))
    if len(digits) < min_digits:
        return None, glyphs, min(scores) if scores else None

    try:
        value = int(''.join(digits))
    except ValueError:
        return None, glyphs, None

    return value, glyphs, min(scores) if scores else None


def _save_digit_templates(digits_text, glyphs):
    if not digits_text or len(digits_text) != len(glyphs):
        return

    root = _template_dir()
    save_limit = max(1, int(getattr(cfg, 'BATTLE_GOLD_TEMPLATE_SAVE_LIMIT_PER_DIGIT', 12)))
    for digit, glyph in zip(digits_text, glyphs):
        digit_dir = root / digit
        digit_dir.mkdir(parents=True, exist_ok=True)
        existing = list(digit_dir.glob('*.png'))
        if len(existing) >= save_limit:
            continue
        file_name = f'{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}.png'
        cv2.imwrite(str(digit_dir / file_name), glyph)


def _bootstrap_from_tesseract(image_rgb, glyphs):
    if not bool(getattr(cfg, 'BATTLE_GOLD_TEMPLATE_BOOTSTRAP_ENABLED', True)):
        return None

    observed_values = []
    observed_digits = []
    psm_modes = tuple(getattr(cfg, 'BATTLE_GOLD_OCR_PSM_MODES', (7, 6, 13)))
    for frame in _ocr_frame_candidates(image_rgb):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        try:
            cv2.imwrite(tmp_path, frame)
            for psm in psm_modes:
                raw_text = _run_tesseract(tmp_path, psm)
                values = _extract_values_from_ocr_text(raw_text)
                observed_values.extend(values)
                normalized = _normalize_ocr_text(raw_text)
                if normalized is not None:
                    observed_digits.append(str(normalized))
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    stable_value = _select_stable_gold_value(observed_values)
    if stable_value is None:
        return None

    stable_text = str(stable_value)
    if glyphs and len(glyphs) == len(stable_text):
        _save_digit_templates(stable_text, glyphs)
    return stable_value


def _read_by_ocr(image_rgb):
    observed_values = []
    raw_samples = []
    psm_modes = tuple(getattr(cfg, 'BATTLE_GOLD_OCR_PSM_MODES', (7, 6, 13)))
    for frame in _ocr_frame_candidates(image_rgb):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        try:
            cv2.imwrite(tmp_path, frame)
            for psm in psm_modes:
                raw_text = _run_tesseract(tmp_path, psm)
                cleaned = _clean_raw_ocr_text(raw_text)
                if cleaned:
                    raw_samples.append(cleaned)
                observed_values.extend(_extract_values_from_ocr_text(cleaned))
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    return _select_stable_gold_value(observed_values), observed_values, raw_samples


def _ocr_frame_candidates(image_rgb):
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    resized = cv2.resize(gray, None, fx=4.5, fy=4.5, interpolation=cv2.INTER_CUBIC)
    _, otsu = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    inv = cv2.bitwise_not(otsu)
    blur = cv2.GaussianBlur(resized, (3, 3), 0)
    _, blur_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        resized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        4,
    )
    return [resized, otsu, inv, blur_otsu, adaptive]


def _read_frame(image_rgb):
    ocr_value, ocr_candidates, raw_samples = _read_by_ocr(image_rgb)
    if ocr_value is not None:
        return ocr_value, 'ocr', ocr_candidates, raw_samples

    if bool(getattr(cfg, 'BATTLE_GOLD_USE_TEMPLATE_FALLBACK', False)):
        template_value, glyphs, _ = _read_by_templates(image_rgb)
        if template_value is not None:
            return template_value, 'template', [template_value], raw_samples
        bootstrap_value = _bootstrap_from_tesseract(image_rgb, glyphs)
        if bootstrap_value is not None:
            return bootstrap_value, 'bootstrap', [bootstrap_value], raw_samples

    return None, 'ocr', ocr_candidates, raw_samples

def _read_stage(region, frames):
    observed_values = []
    frame_sources = []
    raw_samples = []
    last_image_rgb = None
    for _ in range(max(1, int(frames))):
        screenshot = pyautogui.screenshot(region=region)
        image_rgb = np.array(screenshot)
        last_image_rgb = image_rgb
        value, source, candidates, frame_raw = _read_frame(image_rgb)
        if value is not None:
            observed_values.append(value)
        elif candidates:
            observed_values.extend(candidates)
        frame_sources.append(source)
        raw_samples.extend(frame_raw[:3])
    return _select_stable_gold_value(observed_values), observed_values, frame_sources, raw_samples[:8], last_image_rgb

def _apply_inner_crop(region, crop):
    left, top, width, height = [int(value) for value in region]
    crop_left, crop_top, crop_right, crop_bottom = [max(0, int(value)) for value in crop]
    inner_left = left + crop_left
    inner_top = top + crop_top
    inner_width = max(1, width - crop_left - crop_right)
    inner_height = max(1, height - crop_top - crop_bottom)
    return inner_left, inner_top, inner_width, inner_height

def _read_numeric_region(region, min_value, inner_crop):
    region = _apply_inner_crop(region, inner_crop)
    quick_frames = max(1, int(getattr(cfg, 'BATTLE_GOLD_TEMPLATE_QUICK_FRAMES', getattr(cfg, 'BATTLE_GOLD_OCR_QUICK_FRAMES', 1))))
    retry_frames = max(quick_frames, int(getattr(cfg, 'BATTLE_GOLD_TEMPLATE_RETRY_FRAMES', getattr(cfg, 'BATTLE_GOLD_OCR_RETRY_FRAMES', 4))))
    accept_margin = int(getattr(cfg, 'BATTLE_GOLD_OCR_ACCEPT_MARGIN', 50000))

    quick_value, quick_candidates, quick_sources, quick_raw, quick_image_rgb = _read_stage(region, quick_frames)
    if quick_value is not None and quick_value >= max(100000, int(min_value) - accept_margin):
        return {
            'value': quick_value,
            'stage': 'quick',
            'candidates': quick_candidates,
            'sources': quick_sources,
            'raw': quick_raw,
            'region': region,
            'image_rgb': quick_image_rgb,
        }

    retry_value, retry_candidates, retry_sources, retry_raw, retry_image_rgb = _read_stage(region, retry_frames)
    payload = {
        'value': retry_value,
        'stage': 'retry',
        'candidates': retry_candidates,
        'sources': retry_sources,
        'raw': retry_raw,
        'region': region,
        'image_rgb': retry_image_rgb,
    }
    return payload


def read_numeric_region(region, min_value=0, inner_crop=(0, 0, 0, 0)):
    return _read_numeric_region(tuple(region), int(min_value), tuple(inner_crop))


def _resource_fallback_regions(resource_name):
    if resource_name == 'elixir':
        regions = getattr(cfg, 'BATTLE_ELIXIR_REGION_FALLBACKS', ())
    else:
        regions = getattr(cfg, 'BATTLE_GOLD_REGION_FALLBACKS', ())
    normalized = []
    for region in regions or ():
        try:
            left, top, width, height = [int(value) for value in region]
        except (TypeError, ValueError):
            continue
        normalized.append((left, top, width, height))
    return normalized


def _read_battle_resource(region, min_value, resource_name='gold'):
    resource_crop = tuple(getattr(cfg, 'BATTLE_GOLD_INNER_CROP', (0, 0, 0, 0)))
    if resource_name == 'elixir':
        resource_crop = tuple(getattr(cfg, 'BATTLE_ELIXIR_INNER_CROP', resource_crop))

    candidate_regions = [tuple(region)]
    for fallback_region in _resource_fallback_regions(resource_name):
        if fallback_region not in candidate_regions:
            candidate_regions.append(fallback_region)

    payloads = [
        _read_numeric_region(candidate_region, min_value, resource_crop)
        for candidate_region in candidate_regions
    ]

    threshold = max(100000, int(min_value) - int(getattr(cfg, 'BATTLE_GOLD_OCR_ACCEPT_MARGIN', 50000)))
    for payload in payloads:
        value = payload.get('value')
        if value is not None and value >= threshold:
            return payload

    scored_payloads = []
    for payload in payloads:
        value = payload.get('value')
        if value is None:
            scored_payloads.append((-1, -1, payload))
            continue
        scored_payloads.append((
            len(str(int(value))),
            max(payload.get('candidates', [value])) if payload.get('candidates') else int(value),
            payload,
        ))
    best_payload = max(scored_payloads, key=lambda item: (item[0], item[1]))[2]
    if best_payload.get('value') is None and best_payload.get('image_rgb') is not None:
        _save_bad_resource_read(
            best_payload['image_rgb'],
            resource_name,
            best_payload.get('region', region),
            best_payload.get('stage', 'retry'),
            best_payload.get('raw', []),
        )
    return best_payload


def read_battle_loot():
    gold_region = tuple(lcfg.get_region('BATTLE_GOLD_REGION', getattr(cfg, 'BATTLE_GOLD_REGION', (58, 188, 240, 42))))
    elixir_region = tuple(lcfg.get_region('BATTLE_ELIXIR_REGION', getattr(cfg, 'BATTLE_ELIXIR_REGION', (58, 228, 240, 42))))
    gold_min = lcfg.get_int('BATTLE_GOLD_MIN', 450000)
    return {
        'gold': _read_battle_resource(gold_region, gold_min, 'gold'),
        'elixir': _read_battle_resource(elixir_region, 0, 'elixir'),
    }


def read_battle_gold():
    return read_battle_loot().get('gold', {}).get('value')


def _fmt_candidates(values):
    if not values:
        return '[]'
    return '[' + ','.join(str(int(item)) for item in values[:6]) + (',…' if len(values) > 6 else '') + ']'


def _fmt_raw(values):
    if not values:
        return '[]'
    snippets = [str(item)[:18] for item in values[:4]]
    return '[' + ' | '.join(snippets) + ( ' | …' if len(values) > 4 else '') + ']'


def _log_battle_loot(loot):
    if not lcfg.get_bool('BATTLE_RESOURCE_DEBUG_LOG', True):
        return
    gold = loot.get('gold', {})
    elixir = loot.get('elixir', {})
    text = (
        'Battle loot scan: '
        f'gold={gold.get("value") if gold.get("value") is not None else "n/a"} '
        f'({gold.get("stage", "-")}, {",".join(gold.get("sources", [])[:4]) or "-"}) '
        f'candidates={_fmt_candidates(gold.get("candidates", []))} '
        f'raw={_fmt_raw(gold.get("raw", []))}; '
        f'elixir={elixir.get("value") if elixir.get("value") is not None else "n/a"} '
        f'({elixir.get("stage", "-")}, {",".join(elixir.get("sources", [])[:4]) or "-"}) '
        f'candidates={_fmt_candidates(elixir.get("candidates", []))} '
        f'raw={_fmt_raw(elixir.get("raw", []))}'
    )
    print(text)
    telegram_reporter.append_console_log(text)


def ensure_min_gold_before_attack(wait_for_army_ready_screen_fn):
    if not lcfg.get_bool('ENABLE_BATTLE_GOLD_FILTER', False):
        return True

    min_gold = lcfg.get_int('BATTLE_GOLD_MIN', 450000)
    min_elixir = lcfg.get_int('BATTLE_ELIXIR_MIN', min_gold)
    accept_on_unknown = lcfg.get_bool('BATTLE_GOLD_ACCEPT_ON_UNKNOWN', True)
    unreliable_below = max(0, lcfg.get_int('BATTLE_GOLD_UNRELIABLE_BELOW', 50000))
    reroll_key = lcfg.get_str('BATTLE_GOLD_REROLL_KEY', 'enter').strip().lower() or 'enter'
    reroll_sleep = max(0.0, lcfg.get_float('BATTLE_GOLD_REROLL_SLEEP', 0.8))
    max_rerolls = max(0, lcfg.get_int('BATTLE_GOLD_OCR_MAX_REROLLS', 200))
    reroll_count = 0

    while True:
        loot = read_battle_loot()
        _log_battle_loot(loot)
        gold_value = loot.get('gold', {}).get('value')
        elixir_value = loot.get('elixir', {}).get('value')
        if gold_value is None:
            if accept_on_unknown:
                print('Loot filter unreadable. Keep current target.')
                telegram_reporter.append_console_log('Loot filter: unreadable value, keep current target.')
                return True
            print(f'Loot filter reroll: gold=n/a elixir={elixir_value if elixir_value is not None else "n/a"}')
            telegram_reporter.append_console_log(f'Loot filter reroll: gold=n/a elixir={elixir_value if elixir_value is not None else "n/a"}')
            pyautogui.press(reroll_key)
            if reroll_sleep > 0:
                pyautogui.sleep(reroll_sleep)
            reroll_count += 1
            if reroll_count >= max_rerolls:
                print(f'Loot filter reached reroll limit ({max_rerolls}) on unreadable OCR. Continue with current target.')
                return True
            if not wait_for_army_ready_screen_fn():
                return False
            continue

        if gold_value is not None and gold_value < unreliable_below:
            print(f'Loot filter uncertain OCR ({gold_value} < {unreliable_below}). Keep current target.')
            telegram_reporter.append_console_log(f'Loot filter: uncertain OCR {gold_value} < {unreliable_below}, keep current target.')
            return True

        if elixir_value is None:
            if accept_on_unknown:
                print('Loot filter unreadable elixir. Keep current target.')
                telegram_reporter.append_console_log('Loot filter: unreadable elixir, keep current target.')
                return True
            print(f'Loot filter reroll: gold={gold_value} elixir=n/a')
            telegram_reporter.append_console_log(f'Loot filter reroll: gold={gold_value} elixir=n/a')
            pyautogui.press(reroll_key)
            if reroll_sleep > 0:
                pyautogui.sleep(reroll_sleep)
            reroll_count += 1
            if reroll_count >= max_rerolls:
                print(f'Loot filter reached reroll limit ({max_rerolls}) on unreadable OCR. Continue with current target.')
                return True
            if not wait_for_army_ready_screen_fn():
                return False
            continue

        if gold_value >= min_gold and elixir_value >= min_elixir:
            print(f'Loot filter accepted target: gold={gold_value} elixir={elixir_value}')
            telegram_reporter.append_console_log(f'Loot filter accepted: gold={gold_value} elixir={elixir_value}')
            return True

        if reroll_count >= max_rerolls:
            print(f'Loot filter reached reroll limit ({max_rerolls}). Continue with current target.')
            return True

        print(
            f'Loot filter reroll: gold={gold_value if gold_value is not None else "n/a"} < {min_gold} '
            f'or elixir={elixir_value if elixir_value is not None else "n/a"} < {min_elixir}'
        )
        telegram_reporter.append_console_log(
            f'Loot filter reroll: gold={gold_value if gold_value is not None else "n/a"} < {min_gold} '
            f'or elixir={elixir_value if elixir_value is not None else "n/a"} < {min_elixir}'
        )
        pyautogui.press(reroll_key)
        if reroll_sleep > 0:
            pyautogui.sleep(reroll_sleep)
        reroll_count += 1

        if not wait_for_army_ready_screen_fn():
            return False
