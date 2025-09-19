import React from 'react';
import { Paperclip, Loader, X, Check } from 'lucide-react';

interface AttachedFileIndicatorProps {
  fileName: string;
  isProcessing: boolean;
  onRemove: () => void;
}

const AttachedFileIndicator: React.FC<AttachedFileIndicatorProps> = ({ fileName, isProcessing, onRemove }) => {
  return (
    <div className="flex items-center justify-between bg-green-50 rounded-lg px-3 py-2 mb-2 text-sm border border-green-200">
      <div className="flex items-center gap-2">
        <Paperclip className="w-4 h-4 text-green-700" />
        <span className="text-green-800 font-medium truncate">{fileName}</span>
      </div>
      <div className="flex items-center gap-2">
        {isProcessing ? (
          <Loader className="w-4 h-4 text-green-700 animate-spin" />
        ) : (
          <>
            <Check className="w-4 h-4 text-green-600" />
            <button 
              type="button" 
              onClick={onRemove} 
              className="text-green-600 hover:text-red-700"
              title="Remove file context"
            >
              <X className="w-4 h-4" />
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default AttachedFileIndicator;
