"""
SCOUT Backend - Main FastAPI Application
AI system that takes business plans and outputs GO/NO-GO decisions with comprehensive market intelligence reports.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import asyncio 
import json
from typing import List, Dict, Any, AsyncGenerator
import logging
from datetime import datetime
from agents.planner_agent import chat_with_planner, chat_with_planner_streaming
from config.settings import settings
from storage.local import LocalStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SCOUT AI System",
    description="AI system that takes business plans and outputs GO/NO-GO decisions with comprehensive market intelligence reports",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage client based on settings
if settings.storage_backend == 'local':
    storage_client = LocalStorage()
else:
    # Placeholder for other storage clients like S3
    # from storage.s3 import S3Storage
    # storage_client = S3Storage()
    raise NotImplementedError(f"Storage backend '{settings.storage_backend}' not implemented")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "SCOUT AI System is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# File upload endpoint
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the configured storage backend.
    """
    try:
        content = await file.read()
        file_path = storage_client.save_file(file.filename, content)
        
        return {
            "message": "File uploaded successfully",
            "file_path": file_path
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Get analysis status endpoint
@app.get("/api/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    """
    Get the current status of a business plan analysis
    """
    # TODO: Implement actual status tracking
    return {
        "analysis_id": analysis_id,
        "status": "processing",
        "progress": 0,
        "current_agent": "planner",
        "estimated_completion": "2024-01-01T12:00:00Z"
    }

# Get analysis results endpoint
@app.get("/api/analysis/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """
    Get the final analysis results and report
    """
    # TODO: Implement actual results retrieval
    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "recommendation": "GO",
        "confidence_score": 85,
        "report_url": f"/api/reports/{analysis_id}.pdf"
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{analysis_id}")
async def websocket_endpoint(websocket: WebSocket, analysis_id: str):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and send periodic updates
            await asyncio.sleep(1)
            # TODO: Send actual progress updates from agents
            await manager.send_personal_message(
                json.dumps({
                    "type": "progress_update",
                    "analysis_id": analysis_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Processing business plan..."
                }),
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Chat endpoint for Planner Agent
@app.post("/api/chat")
async def chat_endpoint(request: Dict[str, str]):
    """Chat with the Planner Agent"""
    message = request.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    
    response = chat_with_planner(message)
    return {"response": response}

# Streaming chat endpoint for Planner Agent
@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: Dict[str, str]):
    """Stream chat with the Planner Agent"""
    message = request.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        async for event in chat_with_planner_streaming(message):
            if 'event' in event:
                event_data = event['event']
                if 'contentBlockStart' in event_data:
                    start_data = event_data.get('contentBlockStart', {}).get('start')
                    if start_data and 'toolUse' in start_data:
                        tool_use_data = start_data['toolUse']
                        tool_name = tool_use_data.get('name')
                        tool_use_id = tool_use_data.get('toolUseId')
                        content_block_index = event_data.get('contentBlockStart', {}).get('contentBlockIndex')
                        yield f"data: {json.dumps({'tool_start': {'tool_name': tool_name, 'tool_use_id': tool_use_id, 'content_block_index': content_block_index}})}\n\n"
                elif 'contentBlockStop' in event_data:
                    content_block_index = event_data.get('contentBlockStop', {}).get('contentBlockIndex')
                    yield f"data: {json.dumps({'tool_end': {'content_block_index': content_block_index}})}\n\n"
                elif 'contentBlockDelta' in event_data:
                    delta = event_data.get('contentBlockDelta', {}).get('delta')
                    if delta and 'text' in delta:
                        yield f"data: {json.dumps({'content': delta['text']})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

# Start conversation endpoint
@app.post("/api/chat/start")
async def start_conversation():
    """Start conversation with Planner Agent"""
    return {"response": "Hello! I'm the SCOUT Planner Agent. How can I help you?"}

# Agent status endpoint
@app.get("/api/agents/status")
async def get_agents_status():
    """
    Get the status of all 7 agents
    """
    return {
        "agents": {
            "planner": {"status": "active", "last_activity": datetime.now().isoformat()},
            "orchestrator": {"status": "idle", "last_activity": None},
            "competition": {"status": "idle", "last_activity": None},
            "market": {"status": "idle", "last_activity": None},
            "financial": {"status": "idle", "last_activity": None},
            "risk": {"status": "idle", "last_activity": None},
            "synthesis": {"status": "idle", "last_activity": None}
        },
        "system_status": "operational"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
