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

const ChatBubble: React.FC<ChatBubbleProps> = ({ role, content, tool_name, tool_is_active, attachedFile }) => {
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
          <div className="text-white rounded-3xl px-5 py-3 shadow-sm" style={{ backgroundColor: '#04331c' }}>
            <p className="text-sm leading-relaxed">{displayContent || " "}</p>
          </div>
        </div>
      </div>
    );
  }

  if (tool_name) {
    return (
      <div className="mb-8">
        <ToolIndicator toolName={tool_name} isActive={tool_is_active || false} />
      </div>
    );
  }

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