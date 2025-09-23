# Orchestrator Events Implementation

This implementation captures real-time orchestrator agent events (tool usage, reasoning, text generation) and streams them to the frontend via WebSocket.

## Architecture

```
Orchestrator Agent (port 9001)
    ↓ (callback handler)
Redis Pub/Sub
    ↓ (subscriber)
Main.py (port 8000)
    ↓ (WebSocket)
Frontend Component
```

## Components

### 1. Callback Handler (`orchestrator_agent.py`)
- `OrchestratorEventHandler` class captures real agent events
- Publishes events to Redis channel `orchestrator_events`
- Captures: text generation, tool usage, reasoning

### 2. Redis Bridge (`main.py`)
- Subscribes to Redis `orchestrator_events` channel
- Broadcasts events to WebSocket clients via `/ws/orchestrator`
- Handles connection management and error recovery

### 3. Frontend Component (`OrchestratorComponent.tsx`)
- Connects to WebSocket endpoint `/ws/orchestrator`
- Displays real-time events with icons and formatting
- Auto-scrolls and shows connection status

## Setup & Testing

### 1. Install Dependencies
```bash
cd scout-backend
pip install redis>=4.0.0
```

### 2. Start Redis Server
```bash
# Install Redis if not already installed
# On macOS: brew install redis
# On Ubuntu: sudo apt install redis-server
# On Windows: Use Redis for Windows or Docker

redis-server
```

### 3. Test the Implementation
```bash
# Terminal 1: Start the backend
cd scout-backend
python main.py

# Terminal 2: Test orchestrator events
python test_orchestrator_events.py
# Choose option 1 to listen for events

# Terminal 3: Send test messages
python test_orchestrator_events.py
# Choose option 2 to send test messages
```

### 4. Frontend Testing
1. Start the frontend: `npm run dev`
2. Navigate to the orchestrator component
3. Send messages to the orchestrator via A2A or direct chat
4. Watch real-time events appear in the UI

## Event Types

### Text Generation
```json
{
  "type": "text_generation",
  "data": "I have received your comprehensive research plan...",
  "timestamp": 1703123456.789
}
```

### Tool Usage
```json
{
  "type": "tool_use",
  "tool_name": "store_research_plan",
  "tool_input": {
    "plan_data": "...",
    "source_agent": "planner"
  },
  "timestamp": 1703123456.789
}
```

### Reasoning
```json
{
  "type": "reasoning",
  "content": "I need to store this plan and provide confirmation...",
  "timestamp": 1703123456.789
}
```

## Troubleshooting

### Redis Connection Issues
- Ensure Redis server is running: `redis-cli ping`
- Check Redis logs for connection errors
- Verify Redis is accessible on localhost:6379

### WebSocket Connection Issues
- Check browser console for WebSocket errors
- Verify main.py is running on port 8000
- Check CORS settings for WebSocket connections

### No Events Appearing
- Verify callback handler is attached to orchestrator agent
- Check Redis pub/sub with: `redis-cli monitor`
- Ensure orchestrator is receiving and processing messages

## Production Considerations

1. **Redis Security**: Configure Redis authentication and network security
2. **Error Handling**: Add more robust error handling and reconnection logic
3. **Rate Limiting**: Implement rate limiting for WebSocket connections
4. **Event Filtering**: Add filtering options for different event types
5. **Persistence**: Consider persisting events for replay/debugging