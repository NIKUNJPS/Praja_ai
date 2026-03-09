"""
WebSocket Connection Manager for Real-Time Live Alerts
Supports multiple clients with broadcast capability
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import logging
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)


class AsyncConnectionManager:
    """
    Manages multiple WebSocket connections with broadcast support
    Thread-safe, async-friendly, production-grade
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept and register new WebSocket connection"""
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
        logger.info(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection safely"""
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected clients
        Non-blocking, safe exception handling
        """
        if not self.active_connections:
            return

        logger.info(f"📡 Broadcasting to {len(self.active_connections)} clients: {message.get('type')}")

        # Create tasks for all sends (non-blocking)
        tasks = []
        for connection in self.active_connections[:]:  # Copy list to avoid modification during iteration
            tasks.append(self._safe_send(connection, message))

        # Wait for all sends to complete
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_send(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message with exception handling"""
        try:
            await websocket.send_text(json.dumps(message))
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            await self.disconnect(websocket)

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcast structured event to all clients

        Args:
            event_type: Type of event (civic_work_created, notifications_generated, etc.)
            data: Event payload
        """
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast(message)

    async def heartbeat(self, websocket: WebSocket):
        """Send periodic heartbeat to keep connection alive"""
        try:
            while True:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                await websocket.send_text(json.dumps({
                    "type": "ping",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            await self.disconnect(websocket)


# Global connection manager instance
connection_manager = AsyncConnectionManager()