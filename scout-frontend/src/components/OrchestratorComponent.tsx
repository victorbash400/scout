import React, { useState, useEffect, useRef } from 'react';
import { Target, CheckCircle } from 'lucide-react';

interface OrchestratorStep {
  step: string;
}

interface OrchestratorComponentProps {
  isActive?: boolean;
}

const OrchestratorComponent: React.FC<OrchestratorComponentProps> = ({ isActive = false }) => {
  const [steps, setSteps] = useState<OrchestratorStep[]>([]);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [steps]);

  const fetchSteps = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/orchestrator/steps');
      if (!response.ok) {
        throw new Error('Failed to fetch orchestrator steps');
      }
      const data = await response.json();
      setSteps(data.steps || []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error(err);
    }
  };

  useEffect(() => {
    if (isActive) {
      fetchSteps(); // Fetch immediately when activated
      intervalRef.current = setInterval(fetchSteps, 2000); // Poll every 2 seconds
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isActive]);

  return (
    <div className="flex flex-col bg-white rounded-xl max-h-[80vh]">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <Target className="w-5 h-5 text-purple-600" />
          <h2 className="text-md font-semibold text-gray-800">Orchestrator Agent</h2>
        </div>
        <p className="text-xs text-gray-500 mt-1">Executing research plan...</p>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {error && (
          <div className="flex items-center justify-center h-full text-red-500">
            <div className="text-center">
              <p className="text-sm">Error: {error}</p>
            </div>
          </div>
        )}
        {!error && steps.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
              <p className="text-sm">Waiting for orchestrator to start...</p>
            </div>
          </div>
        )}
        {!error && steps.map((step, index) => (
          <div key={index} className="flex items-start gap-3">
            <CheckCircle className="w-4 h-4 text-green-500 mt-1 flex-shrink-0" />
            <span className="text-sm text-gray-700">{step.step}</span>
          </div>
        ))}
        <div ref={eventsEndRef} />
      </div>
      
      <div className="p-3 border-t border-gray-200 text-xs text-gray-400 flex items-center justify-between">
        <span>Polling for updates</span>
        <span>{steps.length} steps</span>
      </div>
    </div>
  );
};

export default OrchestratorComponent;
