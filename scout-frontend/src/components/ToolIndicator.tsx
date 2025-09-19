import React from 'react';

interface ToolIndicatorProps {
  toolName: string;
  isActive: boolean;
}

const ToolIndicator: React.FC<ToolIndicatorProps> = ({ toolName, isActive }) => {
  if (!isActive) return null;

  return (
    <div className="inline-flex items-center gap-2 px-2 py-1 bg-white border border-green-700 rounded-md text-xs">
      <span className="text-gray-700 font-medium truncate max-w-xs">
        Using {toolName}...
      </span>
    </div>
  );
};

export default ToolIndicator;

