import React from 'react';

interface ChatBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ role, content, timestamp }) => {
  if (role === 'user') {
    return (
      <div className="flex justify-end mb-8">
        <div className="text-white rounded-3xl px-5 py-3 max-w-md shadow-sm" style={{backgroundColor: '#64756a'}}>
          <p className="text-base leading-relaxed">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-8">
      <div className="w-full text-gray-900">
        <div className="text-lg font-normal text-left prose prose-lg max-w-none" style={{ lineHeight: '1.8' }}>
          <p className="text-left mb-4">{content}</p>
        </div>
      </div>
    </div>
  );
};

export default ChatBubble;
