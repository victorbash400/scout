import React, { useRef, useEffect } from 'react';
import ChatBubble from './chatbubble';
import ChatInput from './chatinput';
import PlanComponent from '../components/PlanComponent';
import UpdateComponent from '../components/UpdateComponent';


interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tool_name?: string;
  tool_input?: any;
  tool_is_active?: boolean;
  attachedFile?: {
    name: string;
    processed: boolean;
  } | null;
}

interface TodoList {
  competition_tasks: string[];
  market_tasks: string[];
  financial_tasks: string[];
  risk_tasks: string[];
  synthesis_requirements: string[];
  price_tasks: string[];
  legal_tasks: string[];
}

interface ChatSectionProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  attachedFile: File | null;
  isProcessingFile: boolean;
  onFileAttach: (file: File) => void;
  onRemoveAttachment: () => void;
  mode?: 'chat' | 'agent';
  todoList?: TodoList | null;
  activeToolCalls?: Set<string>;
  isExecutingPlan?: boolean;
  generatedReports?: { name: string; path: string }[];
  onNewEvent?: (event: any) => void;
}

const ChatSection: React.FC<ChatSectionProps> = ({
  messages,
  onSendMessage,
  isLoading = false,
  attachedFile,
  isProcessingFile,
  onFileAttach,
  onRemoveAttachment,
  mode = 'chat',
  todoList = null,
  activeToolCalls = new Set(),
  isExecutingPlan = false,
  generatedReports = [],
  onNewEvent = () => {},
}) => {
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <div className="h-screen flex">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Chat messages area */}
        <div ref={chatContainerRef} className="flex-1 overflow-y-auto pt-16 scrollbar-hide">
          <div className="max-w-2xl mx-auto px-8">
            <div className="space-y-8">
              {messages.map((message, index) => (
                <ChatBubble
                  key={index}
                  role={message.role}
                  content={message.content}
                  timestamp={message.timestamp}
                  tool_name={message.tool_name}
                  tool_input={message.tool_input}
                  tool_is_active={message.tool_is_active}
                  attachedFile={message.attachedFile || null}
                />
              ))}
              
              {isLoading && (
                <div className="mb-8">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{
                        backgroundColor: '#04331c',
                        animation: 'pulse-scale 1.5s ease-in-out infinite'
                      }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Bottom chat input */}
        <div>
          <div className="max-w-2xl mx-auto">
            <ChatInput 
              onSendMessage={onSendMessage} 
              disabled={isLoading} 
              attachedFile={attachedFile}
              isProcessingFile={isProcessingFile}
              onFileAttach={onFileAttach}
              onRemoveAttachment={onRemoveAttachment}
              mode={mode}
            />
          </div>
        </div>
      </div>
      
      {/* Show SpecialistAgentMonitor when plan is executing, otherwise show Plan component */}
      {isExecutingPlan ? (
        <div className="w-96 p-4 flex items-center">
          <div className="rounded-xl border border-gray-200 bg-white w-full">
            <UpdateComponent onNewEvent={onNewEvent} generatedReports={generatedReports} />
          </div>
        </div>
      ) : (
        // Plan component for agent mode when plan is not executing
        mode === 'agent' && (activeToolCalls.size > 0 || (todoList && Object.values(todoList).some(category => category.length > 0))) && (
          <div className="w-96 p-4 flex items-center">
            <div className="rounded-xl border border-gray-200 bg-white w-full">
              <PlanComponent todoList={todoList} generatedReports={generatedReports} />
            </div>
          </div>
        )
      )}
    </div>
  );
};

export default ChatSection;