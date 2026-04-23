from __future__ import annotations


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _normalize_png_payload(payload: bytes) -> bytes:
    if not payload:
        return b""
    normalized = payload
    start = normalized.find(PNG_SIGNATURE)
    if start > 0:
        normalized = normalized[start:]
    iend = normalized.rfind(b"IEND")
    if iend != -1:
        trailer_end = iend + 8
        if trailer_end <= len(normalized):
            normalized = normalized[:trailer_end]
    return normalized.replace(b"\r\r\n", b"\n")


def capture_png_bytes(adb_client, timeout: float) -> bytes:
    payload = adb_client.run_command(("exec-out", "screencap", "-p"), timeout=timeout, binary=True)
    normalized = _normalize_png_payload(payload)
    if not normalized.startswith(PNG_SIGNATURE):
        raise RuntimeError("ADB screencap did not return a valid PNG payload")
    return normalized
