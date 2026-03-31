"""
WebSocket Manager — Maturidade TI  
Gerencia conexões WebSocket para chat em tempo real durante as entrevistas.
"""

from typing import Dict
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        # session_id → WebSocket
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, session_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: int):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: int, data: dict):
        """Envia mensagem JSON para uma sessão específica."""
        if session_id in self.active_connections:
            ws = self.active_connections[session_id]
            await ws.send_text(json.dumps(data, ensure_ascii=False))

    async def send_typing(self, session_id: int):
        """Indica que o agente está processando."""
        await self.send_message(session_id, {"type": "typing", "role": "agent"})

    async def send_agent_message(self, session_id: int, content: str, extra: dict = None):
        """Envia mensagem do agente para o cliente."""
        payload = {
            "type": "message",
            "role": "agent",
            "content": content,
        }
        if extra:
            payload.update(extra)
        await self.send_message(session_id, payload)

    async def send_error(self, session_id: int, error: str):
        """Envia erro para o cliente."""
        await self.send_message(session_id, {"type": "error", "content": error})

    async def send_interview_complete(self, session_id: int, assessment_id: int):
        """Notifica que a entrevista foi concluída."""
        await self.send_message(session_id, {
            "type": "interview_complete",
            "assessment_id": assessment_id,
            "message": "Entrevista concluída! Gerando seu feedback..."
        })


manager = ConnectionManager()
