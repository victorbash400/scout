import React, { useState, useEffect, useRef } from 'react';
import { Target, Activity, Zap, Wrench, Brain, CheckCircle, AlertCircle, Cog } from 'lucide-react';

interface OrchestratorEvent {
  type: 'orchestrator_message' | 'connection_established';
  event?: 'text_stream' | 'tool_start' | 'tool_end';
  message?: string;
  timestamp: number | string;
  extra?: {
    tool_name?: string;
    result?: string;
  };
}

interface OrchestratorComponentProps {
  isActive?: boolean;
}

const OrchestratorComponent: React.FC<OrchestratorComponentProps> = ({ isActive = false }) => {
  const [events, setEvents] = useState<OrchestratorEvent[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [currentText, setCurrentText] = useState('');
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [events, currentText]);

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8000/ws/orchestrator');
        wsRef.current = ws;

        ws.onopen = () => {
          setConnectionStatus('connected');
          console.log('Connected to orchestrator events stream');
        };

        ws.onmessage = (event) => {
          try {
            const eventData: OrchestratorEvent = JSON.parse(event.data);
            
            if (eventData.type === 'orchestrator_message') {
              if (eventData.event === 'text_stream') {
                // Accumulate streaming text
                setCurrentText(prev => prev + (eventData.message || ''));
              } else if (eventData.event === 'tool_start') {
                // Flush current text before tool starts
                if (currentText.trim()) {
                  setEvents(prev => [...prev, {
                    type: 'orchestrator_message',
                    event: 'text_stream',
                    message: currentText.trim(),
                    timestamp: Date.now()
                  }]);
                  setCurrentText('');
                }
                setActiveTool(eventData.extra?.tool_name || 'unknown');
                setEvents(prev => [...prev, eventData]);
              } else if (eventData.event === 'tool_end') {
                setActiveTool(null);
                setEvents(prev => [...prev, eventData]);
              }
            } else {
              // Other event types (like connection_established)
              setEvents(prev => [...prev, eventData]);
            }
          } catch (error) {
            console.error('Error parsing orchestrator event:', error);
          }
        };

        ws.onclose = () => {
          setConnectionStatus('disconnected');
          console.log('Disconnected from orchestrator events stream');
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionStatus('disconnected');
        };
      } catch (error) {
        console.error('Error connecting to WebSocket:', error);
        setConnectionStatus('disconnected');
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [currentText]);

  const formatTimestamp = (timestamp: number | string) => {
    const date = typeof timestamp === 'number' ? new Date(timestamp) : new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'text-green-500';
      case 'connecting':
        return 'text-yellow-500';
      case 'disconnected':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getToolIcon = (toolName: string) => {
    switch (toolName?.toLowerCase()) {
      case 'mock_tool':
        return <Cog className="w-4 h-4" />;
      default:
        return <Wrench className="w-4 h-4" />;
    }
  };

  return (
    <div className="flex flex-col bg-white rounded-xl max-h-[80vh]">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <Target className="w-5 h-5 text-purple-600" />
          <h2 className="text-md font-semibold text-gray-800">Orchestrator Agent</h2>
          <div className="ml-auto flex items-center gap-2">
            <Activity className={`w-5 h-5 ${getConnectionStatusColor()}`} />
            <span className={`text-sm font-medium ${getConnectionStatusColor()}`}>
              {connectionStatus === 'connected' ? 'Live' : 
               connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
            </span>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-1">Real-time Agent Activity & Tool Usage</p>
        {activeTool && (
          <div className="mt-2 flex items-center gap-2 text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
            <Cog className="w-3 h-3 animate-spin" />
            <span>Running: {activeTool}</span>
          </div>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {events.length === 0 && !currentText ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Waiting for orchestrator activity...</p>
            </div>
          </div>
        ) : (
          <>
            {events.map((event, index) => (
              <div key={index} className="mb-3">
                {event.type === 'connection_established' && event.message && (
                  <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 p-2 rounded">
                    <CheckCircle className="w-4 h-4" />
                    <span>{event.message}</span>
                  </div>
                )}
                
                {event.type === 'orchestrator_message' && (
                  <>
                    {event.event === 'text_stream' && event.message && (
                      <div className="text-sm text-gray-800 bg-gray-50 p-3 rounded-lg">
                        <div className="whitespace-pre-wrap">{event.message}</div>
                      </div>
                    )}
                    
                    {event.event === 'tool_start' && (
                      <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 p-2 rounded">
                        {getToolIcon(event.extra?.tool_name || '')}
                        <span>{event.message}</span>
                      </div>
                    )}
                    
                    {event.event === 'tool_end' && (
                      <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 p-2 rounded">
                        <CheckCircle className="w-4 h-4" />
                        <span>{event.message}</span>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
            
            {/* Current streaming text */}
            {currentText.trim() && (
              <div className="text-sm text-gray-800 bg-gray-50 p-3 rounded-lg border-l-4 border-blue-400">
                <div className="whitespace-pre-wrap">{currentText}</div>
                <div className="inline-block w-2 h-4 bg-blue-400 animate-pulse ml-1"></div>
              </div>
            )}
          </>
        )}
        <div ref={eventsEndRef} />
      </div>
      
      <div className="p-3 border-t border-gray-200 text-xs text-gray-400 flex items-center justify-between">
        <span>Real-time orchestrator events via WebSocket</span>
        <span>{events.length} events</span>
      </div>
    </div>
  );
};

export default OrchestratorComponent;