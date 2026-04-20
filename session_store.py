"""
Gestión de sesiones de conversación por número de teléfono.
Un SalesAgent por usuario, con TTL de 30 minutos de inactividad.
"""

import json
import os
import time
from dataclasses import dataclass, field

from agent import SalesAgent
from config import Config


SESSION_TTL_SECONDS = 30 * 60  # 30 minutos
HISTORY_DIR = "chat_history"


@dataclass
class _Session:
    agent: SalesAgent
    last_active: float = field(default_factory=time.time)


class SessionStore:
    def __init__(self, config: Config):
        self._config = config
        self._sessions: dict[str, _Session] = {}
        os.makedirs(HISTORY_DIR, exist_ok=True)

    def _history_path(self, phone: str) -> str:
        safe = phone.replace("+", "").replace(" ", "_")
        return os.path.join(HISTORY_DIR, f"{safe}.json")

    def save_history(self, phone: str, agent: SalesAgent) -> None:
        """Persiste el historial de conversación en disco."""
        path = self._history_path(phone)
        serializable = []
        for msg in agent.history:
            if isinstance(msg, dict):
                serializable.append(msg)
            else:
                # ChatCompletionMessage → dict
                serializable.append(msg.model_dump())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)

    def get_or_create(self, phone: str, phone_number: str = None) -> SalesAgent:
        """
        Retorna el SalesAgent activo para el número dado.

        - Si existe sesión y no expiró → la reutiliza (conversación continúa).
        - Si expiró o no existe → crea una nueva (historial se reinicia).

        La limpieza es lazy: se detecta al acceder, no en background.
        """
        print(f"[SESSION] phone={phone}")
        now = time.time()
        session = self._sessions.get(phone)

        if session is not None:
            if (now - session.last_active) < SESSION_TTL_SECONDS:
                session.last_active = now
                return session.agent
            # Sesión expirada — la reemplazamos
            del self._sessions[phone]

        new_agent = SalesAgent(self._config, phone=phone)
        self._sessions[phone] = _Session(agent=new_agent, last_active=now)
        return new_agent

    @property
    def active_sessions(self) -> int:
        """Cantidad de sesiones activas (útil para el health check futuro)."""
        now = time.time()
        return sum(
            1
            for s in self._sessions.values()
            if (now - s.last_active) < SESSION_TTL_SECONDS
        )
