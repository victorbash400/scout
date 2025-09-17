import React, { useRef, useEffect } from 'react';
import ChatBubble from './chatbubble';
import ChatInput from './chatinput';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatSectionProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

const ChatSection: React.FC<ChatSectionProps> = ({ messages, onSendMessage, isLoading = false }) => {
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <div className="h-screen flex flex-col">
      {/* Chat messages area */}
      <div ref={chatContainerRef} className="flex-1 overflow-y-auto pt-16 pb-24 scrollbar-hide">
        <div className="max-w-2xl mx-auto px-8 py-6">
          <div className="space-y-8">
            {messages.map((message, index) => (
              <ChatBubble
                key={index}
                role={message.role}
                content={message.content}
                timestamp={message.timestamp}
              />
            ))}
            
            {isLoading && (
              <div className="mb-8">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-1">
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse"></div>
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                  <span className="text-sm text-gray-500">AI is thinking...</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Floating bottom chat input */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent p-6">
        <div className="max-w-2xl mx-auto">
          <ChatInput onSendMessage={onSendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
};

export default ChatSection;
