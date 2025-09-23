"""
SCOUT Backend - Main FastAPI Application
AI system that takes business plans and outputs GO/NO-GO decisions with comprehensive market intelligence reports.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import asyncio 
import json
import threading
from typing import List, Dict, Any, AsyncGenerator
import logging
from datetime import datetime
from agents.planner_agent import chat_with_planner, chat_with_planner_streaming, set_planner_context, clear_planner_context, get_planner_todo_list, clear_planner_todo_list, create_planner_a2a_server
from agents.orchestrator_agent import create_orchestrator_a2a_server
from config.settings import settings
from storage.local import LocalStorage
from utils.pdf_parser import extract_text_from_pdf

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

# Start A2A agents in background threads
def start_a2a_agents():
    """Start both A2A agents in background threads with health checks"""
    try:
        # Start Planner A2A Server on port 9000
        def run_planner_server():
            planner_server = create_planner_a2a_server(port=9000)
            logger.info("Starting Planner A2A Server on port 9000...")
            planner_server.serve()
        
        planner_thread = threading.Thread(target=run_planner_server, daemon=True)
        planner_thread.start()
        logger.info("✅ Planner A2A Server started in background")
        
        # Start Orchestrator A2A Server on port 9001
        def run_orchestrator_server():
            orchestrator_server = create_orchestrator_a2a_server(port=9001)
            logger.info("Starting Orchestrator A2A Server on port 9001...")
            orchestrator_server.serve()
        
        orchestrator_thread = threading.Thread(target=run_orchestrator_server, daemon=True)
        orchestrator_thread.start()
        logger.info("✅ Orchestrator A2A Server started in background")
        
        # Give servers more time to start and add health check
        import time
        time.sleep(5)  # Increased from 2 seconds
        
        # Health check for A2A servers
        try:
            import httpx
            with httpx.Client(timeout=5.0) as client:
                # Check planner agent card
                planner_response = client.get("http://127.0.0.1:9000/.well-known/agent-card.json")
                if planner_response.status_code == 200:
                    logger.info("✅ Planner A2A Server health check passed")
                else:
                    logger.warning(f"⚠️ Planner A2A Server health check failed: {planner_response.status_code}")
                
                # Check orchestrator agent card
                orchestrator_response = client.get("http://127.0.0.1:9001/.well-known/agent-card.json")
                if orchestrator_response.status_code == 200:
                    logger.info("✅ Orchestrator A2A Server health check passed")
                else:
                    logger.warning(f"⚠️ Orchestrator A2A Server health check failed: {orchestrator_response.status_code}")
        except Exception as health_error:
            logger.warning(f"⚠️ A2A Server health check failed: {health_error}")
        
    except Exception as e:
        logger.error(f"Error starting A2A agents: {e}")

# Start A2A agents
start_a2a_agents()

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

# Webhook endpoint for orchestrator events
@app.post("/api/orchestrator/events")
async def receive_orchestrator_event(request: Request):
    """Receive orchestrator events via HTTP webhook and broadcast to WebSocket clients"""
    try:
        event_data = await request.json()
        
        # Broadcast to all connected WebSocket clients
        await manager.broadcast(json.dumps(event_data))
        
        return {"status": "success", "message": "Event received and broadcasted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process event")

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
    If the file is a PDF, its text content is extracted and set as context.
    """
    try:
        content = await file.read()
        file_path = storage_client.save_file(file.filename, content)
        
        extracted_content = None
        if file.content_type == 'application/pdf':
            logger.info(f"Processing uploaded PDF: {file.filename}")
            extracted_content = extract_text_from_pdf(content)
            if extracted_content:
                set_planner_context(extracted_content)
                logger.info(f"Extracted and set context from {file.filename}")
            else:
                logger.warning(f"Could not extract text from PDF: {file.filename}")

        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "content": extracted_content
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/context/clear")
async def clear_context():
    """Clears the document context from the planner agent."""
    try:
        clear_planner_context()
        clear_planner_todo_list()  # Also clear the to-do list when clearing context
        logger.info("Document context and to-do list cleared.")
        return {"message": "Context and to-do list cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear context")

# Get to-do list endpoint
@app.get("/api/plan/todo")
async def get_todo_list():
    """Get the current to-do list from the planner agent."""
    try:
        todo_list = get_planner_todo_list()
        return {"todo_list": todo_list}
    except Exception as e:
        logger.error(f"Error retrieving to-do list: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve to-do list")

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
            await asyncio.sleep(60)  # Just keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# WebSocket endpoint for orchestrator events
@app.websocket("/ws/orchestrator")
async def orchestrator_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time orchestrator events"""
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            json.dumps({
                "type": "connection_established",
                "message": "Connected to orchestrator events stream",
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Chat endpoint for Planner Agent
@app.post("/api/chat")
async def chat_endpoint(request: Dict[str, str]):
    """Chat with the Planner Agent"""
    message = request.get("message", "")
    mode = request.get("mode", "chat")  # Default to chat mode
    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    
    # Prepend mode information to the message
    mode_prefix = f"[MODE: {mode.upper()}] "
    prefixed_message = mode_prefix + message
    
    response = chat_with_planner(prefixed_message)
    return {"response": response}

# Streaming chat endpoint for Planner Agent
@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: Dict[str, str]):
    """Stream chat with the Planner Agent"""
    message = request.get("message", "")
    mode = request.get("mode", "chat")  # Default to chat mode
    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    
    # Prepend mode information to the message
    mode_prefix = f"[MODE: {mode.upper()}] "
    prefixed_message = mode_prefix + message
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        async for event in chat_with_planner_streaming(prefixed_message):
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
    Get the status of all agents including A2A agents
    """
    return {
        "agents": {
            "planner": {"status": "active", "last_activity": datetime.now().isoformat(), "port": 8000},
            "planner_a2a": {"status": "active", "last_activity": datetime.now().isoformat(), "port": 9000},
            "orchestrator_a2a": {"status": "active", "last_activity": datetime.now().isoformat(), "port": 9001},
            "competition": {"status": "idle", "last_activity": None},
            "market": {"status": "idle", "last_activity": None},
            "financial": {"status": "idle", "last_activity": None},
            "risk": {"status": "idle", "last_activity": None},
            "synthesis": {"status": "idle", "last_activity": None}
        },
        "system_status": "operational",
        "a2a_communication": "enabled"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
