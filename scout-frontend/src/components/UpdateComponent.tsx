import React, { useEffect, useState, useRef } from 'react';
import ReportLink from './ReportLink';

interface StreamEvent {
    eventId: string;
    timestamp: number;
    agentName: string;
    eventType: 'thought_start' | 'thought_delta' | 'thought_end' | 'tool_call' | 'tool_output';
    payload: any;
    traceId: string;
    spanId: string;
    parentSpanId?: string;
}

interface Report {
    name: string;
    path: string;
}

interface UpdateComponentProps {
    onNewEvent?: (event: StreamEvent) => void;
    generatedReports?: Report[];
}

const UpdateComponent: React.FC<UpdateComponentProps> = ({ onNewEvent, generatedReports = [] }) => {
    const [events, setEvents] = useState<StreamEvent[]>([]);
    const eventsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const eventSource = new EventSource('http://localhost:8000/api/specialist/stream');

        eventSource.onmessage = (event) => {
            if (event.data.startsWith(':')) return; // Ignore keepalive pings
            const newEvent: StreamEvent = JSON.parse(event.data);
            setEvents(prevEvents => [...prevEvents, newEvent]);
            if (onNewEvent) {
                onNewEvent(newEvent);
            }
        };

        eventSource.onerror = (error) => {
            console.error('EventSource failed:', error);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, []);

    // Scroll to bottom when new events come in
    useEffect(() => {
        eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [events]);

    const renderEvent = (event: StreamEvent, index: number) => {
        const isProgressEvent = event.eventType === 'tool_call' && event.payload.tool_name === 'update_work_progress' && event.payload.display_message;
        // Find all progress events for vertical line
        const progressEvents = events.filter(e => e.eventType === 'tool_call' && e.payload.tool_name === 'update_work_progress' && e.payload.display_message);
        const progressIndex = isProgressEvent ? progressEvents.findIndex(e => e.eventId === event.eventId) : -1;
        const isCompleted = progressIndex > -1 && progressIndex < progressEvents.length - 1;
        const isCurrent = progressIndex === progressEvents.length - 1;

        switch (event.eventType) {
            case 'thought_start':
                // Don't render thought start events to avoid clutter
                return null;
            case 'thought_delta':
                return (
                    <span
                        key={event.eventId}
                        className={`text-sm text-gray-800 relative`}
                    >
                        {event.payload.text}
                    </span>
                );
            case 'thought_end':
                // Don't render thought end events to avoid clutter
                return null;
            case 'tool_call':
                if (isProgressEvent) {
                    return (
                        <div key={event.eventId} className="flex items-stretch text-xs text-gray-800 min-h-10">
                            {/* Timeline indicator column */}
                            <div className="flex flex-col items-center mr-4" style={{ minWidth: '24px' }}>
                                {/* Top connector */}
                                <div className={`w-px flex-grow ${progressIndex > 0 ? 'bg-gray-300' : ''}`} />

                                {/* Status indicator */}
                                <div className="w-4 h-4 flex-shrink-0 flex items-center justify-center z-10">
                                    {isCompleted ? (
                                        <div className="w-4 h-4 bg-black rounded-full flex items-center justify-center">
                                            <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                            </svg>
                                        </div>
                                    ) : isCurrent ? (
                                        <div className="w-4 h-4 border-2 border-gray-400 border-t-black rounded-full animate-spin"></div>
                                    ) : (
                                        <div className="w-4 h-4 border border-gray-300 rounded-full bg-white"></div>
                                    )}
                                </div>

                                {/* Bottom connector */}
                                <div className={`w-px flex-grow ${progressIndex < progressEvents.length - 1 ? 'bg-gray-300' : ''}`} />
                            </div>

                            {/* Content area */}
                            <div className="flex-1 py-1">
                                <span className={isCurrent ? 'shimmer-effect' : ''}>
                                    <span className="text-xs italic text-gray-600 mr-1">({event.agentName})</span>
                                    {event.payload.display_message}
                                </span>
                            </div>
                        </div>
                    );
                } else {
                    return (
                        <div key={event.eventId} className="flex items-center gap-2 text-xs text-gray-600">
                            <span className="w-2 h-2 bg-gray-400 rounded-full inline-block"></span>
                            Tool Call: <span className="font-medium">{event.payload.tool_name || event.payload.name}</span>
                        </div>
                    );
                }
            case 'tool_output':
                return (
                    <div key={event.eventId} className="flex items-center gap-2 text-xs text-purple-600">
                        <span className="w-2 h-2 bg-purple-400 rounded-full inline-block"></span>
                        Tool Output: <span className="font-mono">{event.payload.output}</span>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="flex flex-col bg-white rounded-xl max-h-[80vh] min-w-[320px] shadow border border-gray-200">
            <div className="p-4 border-b border-gray-200">
                <h2 className="text-md font-semibold text-gray-800">Update Component</h2>
                <p className="text-xs text-gray-500 mt-1">Live agent progress updates</p>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
                {events.length > 0 ? (
                    <div className="space-y-2">
                        {events.map((event, index) => renderEvent(event, index))}
                        <div ref={eventsEndRef} />
                    </div>
                ) : (
                    <div className="flex items-center justify-center h-full text-xs text-gray-400">Waiting for agent activity...</div>
                )}
            </div>

            {/* Show generated reports at the bottom of the Update Component */}
            {generatedReports.length > 0 && (
                <div className="p-3 border-t border-gray-200">
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs text-gray-600 font-medium">Generated Reports</span>
                        <span className="text-xs text-gray-400">({generatedReports.length})</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {generatedReports.map(report => (
                            <ReportLink
                                key={report.path}
                                report={report}
                                className="w-full"
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default UpdateComponent;
