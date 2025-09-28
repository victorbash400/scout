from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import json
from typing import List, Dict, Any, AsyncGenerator
import logging
from datetime import datetime
from agents.planner_agent import (
    chat_with_planner_streaming, 
    set_planner_context, 
    clear_planner_context, 
    get_planner_todo_list, 
    clear_planner_todo_list
)
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
    raise NotImplementedError(f"Storage backend '{settings.storage_backend}' not implemented")

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
        clear_planner_todo_list()
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

# Streaming chat endpoint for Planner Agent
@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: Dict[str, str]):
    """Stream chat with the Planner Agent"""
    message = request.get("message", "")
    mode = request.get("mode", "chat")  # Default to chat mode
    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    
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
                    tool_use_id = event_data.get('contentBlockStop', {}).get('toolUseId') # Changed to get toolUseId
                    content_block_index = event_data.get('contentBlockStop', {}).get('contentBlockIndex')
                    yield f"data: {json.dumps({'tool_end': {'tool_use_id': tool_use_id, 'content_block_index': content_block_index}})}\n\n"
                elif 'contentBlockDelta' in event_data:
                    delta = event_data.get('contentBlockDelta', {}).get('delta')
                    if delta and 'text' in delta:
                        yield f"data: {json.dumps({'content': delta['text']})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )