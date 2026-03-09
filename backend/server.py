from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from pathlib import Path
import logging
from datetime import datetime
from database import init_db
from routers import auth, states, booths, citizens, analytics, graph, civic_works
from websocket import connection_manager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="India Civic Intelligence OS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(states.router)
app.include_router(booths.router)
app.include_router(citizens.router)
app.include_router(analytics.router)
app.include_router(graph.router)
app.include_router(civic_works.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

@app.websocket("/ws/live-alerts")
async def websocket_live_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time live alerts
    Supports: civic work events, notifications, health updates
    """
    await connection_manager.connect(websocket)

    try:
        # Send welcome message
        await connection_manager.send_personal_message({
            "type": "connection_established",
            "message": "Connected to ICIOS Live Intelligence",
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await connection_manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ICIOS API"}