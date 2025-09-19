import React, { useState, useRef, useEffect } from 'react';
import { Settings2, MessageCircleMore, SquareMousePointer, Paperclip, X } from 'lucide-react';

// Interface for the component's props
interface ChatInputProps {
  onSendMessage: (message: string, file?: File) => void;
  disabled?: boolean;
}

// Main ChatInput component
const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled = false }) => {
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<'chat' | 'agent'>('chat');
  const [showModeModal, setShowModeModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handles form submission to send a message
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((input.trim() || selectedFile) && !disabled) {
      onSendMessage(input.trim(), selectedFile || undefined);
      setInput('');
      setSelectedFile(null);
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

  // Handles file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  // Triggers file input click
  const handleAttachClick = () => {
    fileInputRef.current?.click();
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
              {selectedFile && (
                <div className="flex items-center justify-between bg-gray-100 rounded-lg px-3 py-2 mb-2 text-sm">
                  <span className="text-gray-700 truncate">{selectedFile.name}</span>
                  <button 
                    type="button" 
                    onClick={() => setSelectedFile(null)} 
                    className="text-gray-500 hover:text-red-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
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
                <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" />
                <button type="button" onClick={handleAttachClick} className="text-gray-500 hover:text-green-600" title="Attach File">
                  <Paperclip className="w-5 h-5" />
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
              disabled={disabled || (!input.trim() && !selectedFile)}
              className="w-10 h-10 rounded-full flex items-center justify-center transition-colors duration-200 disabled:bg-gray-300 disabled:cursor-not-allowed"
              style={{backgroundColor: disabled || (!input.trim() && !selectedFile) ? '#d1d5db' : '#00311e'}}
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
