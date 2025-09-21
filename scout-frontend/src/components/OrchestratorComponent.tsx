import React from 'react';
import { Target, Activity } from 'lucide-react';

interface OrchestratorComponentProps {
  isActive?: boolean;
}

const OrchestratorComponent: React.FC<OrchestratorComponentProps> = ({ isActive = false }) => {
  return (
    <div className="flex flex-col bg-white rounded-xl max-h-[80vh]">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <Target className="w-5 h-5 text-purple-600" />
          <h2 className="text-md font-semibold text-gray-800">Orchestrator Agent</h2>
          <div className="ml-auto flex items-center gap-2 text-gray-500">
            <Activity className="w-5 h-5" />
            <span className="text-sm font-medium">A2A Ready</span>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-1">A2A Communication & Agent Coordination</p>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-center h-full">
          <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      </div>
      
      <div className="p-3 border-t border-gray-200 text-xs text-gray-400">
        Orchestrator Agent coordinates specialist agents for research execution.
      </div>
    </div>
  );
};

export default OrchestratorComponent;
