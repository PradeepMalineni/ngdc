from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


class TachyonError(RuntimeError):
    pass


@dataclass(frozen=True)
class TachyonConfig:
    base_url: str
    api_key: str
    model: str
    chat_path: str = "/v1/chat/completions"
    timeout_secs: int = 60

    @staticmethod
    def from_env() -> "TachyonConfig":
        base_url = os.environ.get("TACHYON_BASE_URL", "").strip()
        api_key = os.environ.get("TACHYON_API_KEY", "").strip()
        model = os.environ.get("TACHYON_MODEL", "").strip()
        chat_path = os.environ.get("TACHYON_CHAT_PATH", "/v1/chat/completions").strip()
        timeout_secs = int(os.environ.get("TACHYON_TIMEOUT_SECS", "60").strip())

        missing = [k for k, v in {
            "TACHYON_BASE_URL": base_url,
            "TACHYON_API_KEY": api_key,
            "TACHYON_MODEL": model,
        }.items() if not v]
        if missing:
            raise TachyonError(f"Missing required env var(s): {', '.join(missing)}")

        return TachyonConfig(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            model=model,
            chat_path=chat_path if chat_path.startswith("/") else f"/{chat_path}",
            timeout_secs=timeout_secs,
        )


class TachyonClient:
    """
    Minimal chat-completions style client.

    Assumes Tachyon exposes an OpenAI-like endpoint:
      POST {TACHYON_BASE_URL}{TACHYON_CHAT_PATH}
      Authorization: Bearer {TACHYON_API_KEY}
    """

    def __init__(self, cfg: TachyonConfig, session: Optional[requests.Session] = None):
        self.cfg = cfg
        self._http = session or requests.Session()

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        extra_body: Optional[Dict[str, Any]] = None,
    ) -> str:
        url = f"{self.cfg.base_url}{self.cfg.chat_path}"
        body: Dict[str, Any] = {
            "model": self.cfg.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if extra_body:
            body.update(extra_body)

        resp = self._http.post(
            url,
            headers={
                "Authorization": f"Bearer {self.cfg.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(body),
            timeout=self.cfg.timeout_secs,
        )

        if resp.status_code >= 400:
            raise TachyonError(f"Tachyon HTTP {resp.status_code}: {resp.text[:2000]}")

        data = resp.json()

        # OpenAI-style: choices[0].message.content
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:  # noqa: BLE001
            raise TachyonError(f"Unexpected Tachyon response shape: {data}") from e

