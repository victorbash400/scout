import React, { useState, useRef, useEffect } from 'react';
import { Settings2, MessageCircleMore, SquareMousePointer } from 'lucide-react';

// Interface for the component's props
interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

// Main ChatInput component
const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled = false }) => {
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<'chat' | 'agent'>('chat');
  const [showModeModal, setShowModeModal] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Handles form submission to send a message
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  // Handles 'Enter' key press to submit, but allows 'Shift+Enter' for new lines
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Handles mode selection
  const handleModeSelect = (selectedMode: 'chat' | 'agent') => {
    setMode(selectedMode);
    setShowModeModal(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowModeModal(false);
      }
    };

    if (showModeModal) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showModeModal]);

  return (
    <div className="w-full max-w-lg mx-auto font-sans">
      <form onSubmit={handleSubmit} className="relative rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.05)] pt-[20px] px-[2px] pb-[2px]" style={{backgroundColor: '#00311e'}}>
        {/* Mode text in the gradient area */}
        <div className="absolute top-2 left-0 right-0 flex items-center justify-center">
          <div className="flex items-center gap-2 text-xs text-white font-medium">
            {mode === 'chat' ? (
              <>
                <MessageCircleMore className="w-3 h-3" />
                <span>Chat Mode</span>
              </>
            ) : (
              <>
                <SquareMousePointer className="w-3 h-3" />
                <span>Agent Mode</span>
              </>
            )}
          </div>
        </div>
        
        <div className="rounded-[22px] bg-white p-3 mt-4">
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <textarea
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  // Auto-resize textarea
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
                onKeyPress={handleKeyPress}
                placeholder="What do wanna do today?"
                className="w-full bg-transparent text-gray-800 placeholder-gray-400 outline-none resize-none text-base pl-2 overflow-hidden"
                rows={1}
                disabled={disabled}
                style={{minHeight: '24px', maxHeight: '120px'}}
              />
              <div className="flex items-center gap-4 pl-2 mt-1">
                <button type="button" className="text-gray-500 hover:text-green-600" title="Voice Input">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </button>
                <button type="button" className="text-gray-500 hover:text-green-600" title="Attach File">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                </button>
                <div className="relative" ref={dropdownRef}>
                  <button 
                    type="button" 
                    className="text-gray-500 hover:text-green-600" 
                    title="Mode"
                    onClick={() => setShowModeModal(!showModeModal)}
                  >
                    <Settings2 className="w-5 h-5" />
                  </button>
                  
                  {/* Tiny Mode Dropdown */}
                  {showModeModal && (
                    <div className="absolute bottom-full right-0 mb-2 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[120px] z-10">
                      <button
                        onClick={() => handleModeSelect('chat')}
                        className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-50 transition-colors flex items-center gap-2 ${
                          mode === 'chat' ? 'text-green-600 bg-green-50' : 'text-gray-700'
                        }`}
                      >
                        <MessageCircleMore className="w-4 h-4" />
                        Chat
                      </button>
                      <button
                        onClick={() => handleModeSelect('agent')}
                        className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-50 transition-colors flex items-center gap-2 ${
                          mode === 'agent' ? 'text-green-600 bg-green-50' : 'text-gray-700'
                        }`}
                      >
                        <SquareMousePointer className="w-4 h-4" />
                        Agent
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <button
              type="submit"
              disabled={disabled || !input.trim()}
              className="w-10 h-10 rounded-full flex items-center justify-center transition-colors duration-200 disabled:bg-gray-300 disabled:cursor-not-allowed"
              style={{backgroundColor: disabled || !input.trim() ? '#d1d5db' : '#00311e'}}
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            </button>
          </div>
        </div>
      </form>

    </div>
  );
};

export default ChatInput;
