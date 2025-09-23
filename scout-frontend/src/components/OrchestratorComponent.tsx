import React, { useState, useEffect, useRef } from 'react';
import { Target, Activity, Zap, Wrench, Brain, CheckCircle, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface OrchestratorEvent {
  type: 'orchestrator_message' | 'connection_established';
  message?: string;
  timestamp: number | string;
}

interface OrchestratorComponentProps {
  isActive?: boolean;
}

const OrchestratorComponent: React.FC<OrchestratorComponentProps> = ({ isActive = false }) => {
  const [events, setEvents] = useState<OrchestratorEvent[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const wsRef = useRef<WebSocket | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [events]);

  useEffect(() => {
    // Connect to orchestrator WebSocket
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
            setEvents(prev => [...prev, eventData]);
          } catch (error) {
            console.error('Error parsing orchestrator event:', error);
          }
        };

        ws.onclose = () => {
          setConnectionStatus('disconnected');
          console.log('Disconnected from orchestrator events stream');
          // Attempt to reconnect after 3 seconds
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
  }, []);



  const formatTimestamp = (timestamp: number | string) => {
    const date = typeof timestamp === 'number' ? new Date(timestamp * 1000) : new Date(timestamp);
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
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {events.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Waiting for orchestrator activity...</p>
            </div>
          </div>
        ) : (
          events.map((event, index) => (
            <div key={index} className="mb-4">
              {event.type === 'connection_established' && event.message && (
                <p className="text-sm text-green-600">{event.message}</p>
              )}
              

              
              {event.type === 'orchestrator_message' && event.message && (
                <div className="text-sm font-normal text-left prose prose-sm max-w-none text-gray-900" style={{ lineHeight: '1.6' }}>
                  <ReactMarkdown>{event.message}</ReactMarkdown>
                </div>
              )}
            </div>
          ))
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
