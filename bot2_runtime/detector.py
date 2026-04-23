import os

from bot_runtime import screen_state

from . import config
from .logger import log


def image_path(name: str) -> str:
    return os.path.join(config.BOT2_IMAGES_DIR, name)


def has_image(name: str) -> bool:
    path = image_path(name)
    if not os.path.exists(path):
        return False
    try:
        return screen_state.locate_image(path, confidence=config.BOT2_CONFIDENCE) is not None
    except Exception as exc:
        log(f'locate failed for {name}: {exc}')
        return False


def has_any(names) -> bool:
    for name in names:
        if has_image(name):
            return True
    return False


def missing_required_templates():
    required = list(config.BOT2_HOME_IMAGES) + list(config.BOT2_ATTACK_READY_IMAGES) + [
        config.BOT2_RETURN_HOME_IMAGE,
        config.BOT2_STAR_BONUS_IMAGE,
    ]
    return [name for name in required if not os.path.exists(image_path(name))]
