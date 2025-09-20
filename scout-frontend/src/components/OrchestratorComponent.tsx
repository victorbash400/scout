import React from 'react';
import { Users } from 'lucide-react';

interface OrchestratorComponentProps {
  streamingResponse: string;
}

const OrchestratorComponent: React.FC<OrchestratorComponentProps> = ({ streamingResponse }) => {
  return (
    <div className="flex flex-col bg-white rounded-xl max-h-[80vh]">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-gray-600" />
          <h2 className="text-md font-semibold text-gray-800">Agent Orchestration</h2>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Orchestrator agent is coordinating specialist agents
        </p>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        <div className="text-center text-gray-500 text-sm">
          <p>Orchestrator agent is streaming responses in the main chat area.</p>
          <p className="mt-2 text-xs">Watch the chat for real-time agent coordination.</p>
        </div>
      </div>
    </div>
  );
};

export default OrchestratorComponent;
