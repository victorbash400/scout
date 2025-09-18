import React from 'react';
import ReactMarkdown from 'react-markdown';
import ToolIndicator from '../components/ToolIndicator';

interface ChatBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  tool_name?: string;
  tool_input?: any;
  tool_is_active?: boolean;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ role, content, timestamp, tool_name, tool_input, tool_is_active }) => {
  if (role === 'user') {
    return (
      <div className="flex justify-end mb-8">
        <div className="text-white rounded-3xl px-5 py-3 max-w-md shadow-sm" style={{backgroundColor: '#64756a'}}>
          <p className="text-sm leading-relaxed">{content}</p>
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