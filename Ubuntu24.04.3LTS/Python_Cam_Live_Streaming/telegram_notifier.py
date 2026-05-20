"""Kirim notifikasi Telegram saat gerakan terdeteksi."""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

DEFAULT_COOLDOWN_SEC = 60.0


def load_env_file(path: str | Path) -> None:
    """Muat KEY=VALUE ke os.environ (tidak menimpa variabel yang sudah ada)."""
    env_path = Path(path)
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


class TelegramNotifier:
    """Kirim pesan/foto ke Telegram dengan cooldown agar tidak spam."""

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        cooldown_sec: float = DEFAULT_COOLDOWN_SEC,
        send_photo: bool = True,
    ) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._cooldown_sec = cooldown_sec
        self._send_photo = send_photo
        self._lock = threading.Lock()
        self._last_sent = 0.0

    @property
    def cooldown_sec(self) -> float:
        return self._cooldown_sec

    @property
    def send_photo(self) -> bool:
        return self._send_photo

    @classmethod
    def from_settings(
        cls,
        bot_token: str | None,
        chat_id: str | None,
        cooldown_sec: float = DEFAULT_COOLDOWN_SEC,
        send_photo: bool = True,
    ) -> TelegramNotifier | None:
        if not bot_token or not chat_id:
            return None
        return cls(bot_token, chat_id, cooldown_sec, send_photo)

    @classmethod
    def from_env(cls) -> TelegramNotifier | None:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        cooldown = float(os.environ.get("TELEGRAM_COOLDOWN_SEC", DEFAULT_COOLDOWN_SEC))
        send_photo = os.environ.get("TELEGRAM_SEND_PHOTO", "1").strip().lower() not in {
            "0",
            "false",
            "no",
        }
        return cls.from_settings(token, chat_id, cooldown, send_photo)

    def notify_motion(self, jpeg_bytes: bytes | None = None) -> None:
        if not self._reserve_slot():
            return
        caption = (
            "🚨 Gerakan terdeteksi\n"
            f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        threading.Thread(
            target=self._send,
            args=(jpeg_bytes, caption),
            daemon=True,
        ).start()

    def _reserve_slot(self) -> bool:
        with self._lock:
            now = time.monotonic()
            if now - self._last_sent < self._cooldown_sec:
                return False
            self._last_sent = now
            return True

    def _send(self, jpeg_bytes: bytes | None, caption: str) -> None:
        try:
            if self._send_photo and jpeg_bytes:
                self._post_photo(jpeg_bytes, caption)
            else:
                self._post_message(caption)
            print("[telegram] Notifikasi gerakan terkirim.")
        except urllib.error.URLError as exc:
            print(f"[telegram] Gagal kirim: {exc}", flush=True)
        except OSError as exc:
            print(f"[telegram] Gagal kirim: {exc}", flush=True)

    def _api_url(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self._bot_token}/{method}"

    def _post_message(self, text: str) -> None:
        payload = urllib.parse.urlencode(
            {"chat_id": self._chat_id, "text": text}
        ).encode()
        req = urllib.request.Request(
            self._api_url("sendMessage"),
            data=payload,
            method="POST",
        )
        self._read_json(req)

    def _post_photo(self, jpeg_bytes: bytes, caption: str) -> None:
        boundary = "----MotionCamBoundary"
        parts: list[bytes] = []

        for name, value in (("chat_id", self._chat_id), ("caption", caption)):
            parts.extend(
                [
                    f"--{boundary}".encode(),
                    f'Content-Disposition: form-data; name="{name}"'.encode(),
                    b"",
                    value.encode(),
                ]
            )

        parts.extend(
            [
                f"--{boundary}".encode(),
                b'Content-Disposition: form-data; name="photo"; filename="motion.jpg"',
                b"Content-Type: image/jpeg",
                b"",
                jpeg_bytes,
                f"--{boundary}--".encode(),
                b"",
            ]
        )

        body = b"\r\n".join(parts)
        req = urllib.request.Request(
            self._api_url("sendPhoto"),
            data=body,
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        self._read_json(req)

    @staticmethod
    def _read_json(req: urllib.request.Request) -> dict:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if not data.get("ok"):
            raise OSError(data.get("description", "Telegram API error"))
        return data
