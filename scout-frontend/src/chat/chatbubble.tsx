import React from 'react';
import ReactMarkdown from 'react-markdown';
import ToolIndicator from '../components/ToolIndicator';
import { Paperclip } from 'lucide-react';

interface ChatBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  tool_name?: string;
  tool_input?: any;
  tool_is_active?: boolean;
  attachedFile?: {
    name: string;
    processed: boolean;
  } | null;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ role, content, timestamp, tool_name, tool_input, tool_is_active, attachedFile }) => {
  // Extract file information if present in content
  let displayContent = content;
  let fileAttachment = attachedFile;
  
  // Check if content starts with the file prefix pattern
  const filePrefixMatch = content.match(/^\(File: ([^\)]+)\) ?(.*)/);
  if (filePrefixMatch) {
    const fileName = filePrefixMatch[1];
    displayContent = filePrefixMatch[2] || "";
    fileAttachment = {
      name: fileName,
      processed: true
    };
  }

  // Detect agent type from content
  const isOrchestrator = content.includes('ORCHESTRATOR:');
  const isSpecialistAgent = content.includes('COMPETITION AGENT:') || 
                           content.includes('MARKET AGENT:') || 
                           content.includes('FINANCIAL AGENT:') || 
                           content.includes('RISK AGENT:') || 
                           content.includes('SYNTHESIS AGENT:');

  if (role === 'user') {
    return (
      <div className="flex justify-end mb-8">
        <div className="max-w-md">
          {fileAttachment && (
            <div className="flex items-center justify-end mb-2">
              <div className="flex items-center gap-1 bg-green-100 rounded-full px-3 py-1 text-xs text-green-800">
                <Paperclip className="w-3 h-3" />
                <span>{fileAttachment.name}</span>
              </div>
            </div>
          )}
          <div className="text-white rounded-3xl px-5 py-3 shadow-sm" style={{backgroundColor: '#04331c'}}>
            <p className="text-sm leading-relaxed">{displayContent || " "}</p>
          </div>
        </div>
      </div>
    );
  }

  if (tool_name) {
    return (
        <div className="mb-8">
            <ToolIndicator toolName={tool_name} isActive={tool_is_active} />
        </div>
    );
  }

  // Handle specialist agent messages (like user messages with black border)
  if (isSpecialistAgent) {
    return (
      <div className="flex justify-end mb-8">
        <div className="max-w-md">
          <div className="text-white rounded-3xl px-5 py-3 shadow-sm border-2 border-gray-800" style={{backgroundColor: '#04331c'}}>
            <p className="text-sm leading-relaxed">{displayContent || " "}</p>
          </div>
        </div>
      </div>
    );
  }

  // Handle orchestrator messages (green border)
  if (isOrchestrator) {
    return (
      <div className="mb-8">
        <div className="w-full text-gray-900">
          <div className="text-base font-normal text-left prose max-w-none border-2 border-green-500 rounded-lg p-4 bg-green-50" style={{ lineHeight: '1.7' }}>
            <div className="text-left mb-4">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Default assistant messages (no special border)
  return (
    <div className="mb-8">
      <div className="w-full text-gray-900">
        <div className="text-base font-normal text-left prose max-w-none" style={{ lineHeight: '1.7' }}>
          <div className="text-left mb-4">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatBubble;