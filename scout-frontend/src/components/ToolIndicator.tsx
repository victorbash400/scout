import React from 'react';

interface ToolIndicatorProps {
  toolName: string;
  isActive: boolean;
}

const ToolIndicator: React.FC<ToolIndicatorProps> = ({ toolName, isActive }) => {
  if (!isActive) return null;

  return (
    <div className="flex items-center gap-2 mb-3 p-2 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex items-center gap-1">
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
      </div>
      <span className="text-sm text-blue-700 font-medium">
        Using {toolName} tool...
      </span>
    </div>
  );
};

export default ToolIndicator;

