import { useState, useEffect } from 'react';
import './App.css';
import ChatSection from './chat/chatsection';
import ChatInput from './chat/chatinput';
import Sidebar from './components/sidebar';
import { getTimeBasedGreeting } from './data/greetings';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tool_name?: string;
  tool_use_id?: string;
  content_block_index?: number;
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
}

interface ChatSession {
  id: string;
  messages: Message[];
  createdAt: Date;
}

function App() {
  const [currentChatId, setCurrentChatId] = useState<string>('');
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [mode, setMode] = useState<'chat' | 'agent'>('chat'); // Add mode state
  const [todoList, setTodoList] = useState<TodoList | null>(null); // Add to-do list state
  const [activeToolCalls, setActiveToolCalls] = useState<Set<string>>(new Set()); // Track active tool calls

  // New state for file handling
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const [fileContext, setFileContext] = useState<string | null>(null);

  // Initialize first chat session
  useEffect(() => {
    const initialChatId = generateChatId();
    setCurrentChatId(initialChatId);
    
    const initialSession: ChatSession = {
      id: initialChatId,
      messages: [],
      createdAt: new Date()
    };
    setChatSessions([initialSession]);
  }, []);

  const handleFileAttach = async (file: File) => {
    setAttachedFile(file);
    setIsProcessingFile(true);
    setFileContext(null); // Clear previous context

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('File upload failed');
      }

      const result = await response.json();
      if (result.content) {
        setFileContext(result.content);
        console.log('File processed and context set.');
      } else {
        console.log('File uploaded but no content processed (not a PDF).');
      }
    } catch (error) {
      console.error('Error uploading or processing file:', error);
      // Optionally, display an error to the user in the UI
      setAttachedFile(null); // Clear the attachment on error
    } finally {
      setIsProcessingFile(false);
    }
  };

  const handleRemoveAttachment = async () => {
    setAttachedFile(null);
    setFileContext(null);
    try {
      await fetch('http://localhost:8000/api/context/clear', { method: 'POST' });
      console.log('Backend context cleared.');
    } catch (error) {
      console.error('Failed to clear backend context:', error);
    }
  };

  // Generate a unique 6-character chat ID
  const generateChatId = () => {
    return Math.random().toString(36).substring(2, 8).toUpperCase();
  };

  // Start a new chat session
  const startNewChat = async () => {
    // Save current chat session if it exists
    if (currentChatId && messages.length > 0) {
      const updatedSessions = chatSessions.map(session => 
        session.id === currentChatId ? { ...session, messages } : session
      );
      setChatSessions(updatedSessions);
    }

    // Clear current messages and file context
    setMessages([]);
    setAttachedFile(null);
    setFileContext(null);
    setHasStarted(false);
    setTodoList(null); // Clear to-do list
    
    // Clear backend context
    try {
      await fetch('http://localhost:8000/api/context/clear', { method: 'POST' });
      console.log('Backend context cleared for new chat.');
    } catch (error) {
      console.error('Failed to clear backend context:', error);
    }

    // Create new chat session
    const newChatId = generateChatId();
    setCurrentChatId(newChatId);
    
    // Add to chat sessions
    const newSession: ChatSession = {
      id: newChatId,
      messages: [],
      createdAt: new Date()
    };
    setChatSessions(prev => [...prev, newSession]);
  };

  // Fetch to-do list from backend
  const fetchTodoList = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/plan/todo');
      if (!response.ok) {
        throw new Error('Failed to fetch to-do list');
      }
      const data = await response.json();
      setTodoList(data.todo_list);
    } catch (error) {
      console.error('Error fetching to-do list:', error);
    }
  };

  // Handle mode change
  const handleModeChange = (newMode: 'chat' | 'agent') => {
    setMode(newMode);
    if (newMode === 'agent') {
      // Fetch to-do list when switching to agent mode
      fetchTodoList();
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!hasStarted) {
      setHasStarted(true);
    }
    
    setIsLoading(true);

    // For the message content, we don't need to include the file prefix since
    // we're showing it visually in the chat bubble
    let messageToSend = content;

    // Add user message with file attachment info
    const userMessage: Message = {
      role: 'user',
      content: messageToSend,
      timestamp: new Date().toLocaleTimeString(),
      attachedFile: attachedFile ? {
        name: attachedFile.name,
        processed: true
      } : null
    };
    setMessages((prev) => [...prev, userMessage]);

    // Clear the file attachment UI but keep backend context for multi-turn conversations
    // Only clear the attachment UI, not the backend context
    setAttachedFile(null);

    // Add empty assistant message that we'll update with streaming content
    const aiMessage: Message = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, aiMessage]);

    try {
      // Call the streaming backend planner agent
      const response = await fetch('http://localhost:8000/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // The backend will use the context set during the file upload
        body: JSON.stringify({ message: content, mode: mode }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let isFirstChunk = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        if (isFirstChunk) {
          setIsLoading(false);
          isFirstChunk = false;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6); // Remove 'data: ' prefix
            if (data === '[DONE]') {
              // Fetch updated to-do list when streaming is complete
              if (mode === 'agent') {
                fetchTodoList();
              }
              break;
            }
            
            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                setMessages((prev) => {
                  const lastMessage = prev[prev.length - 1];
                  if (lastMessage && lastMessage.role === 'assistant' && !lastMessage.tool_name) {
                    return prev.map((msg, i) => (i === prev.length - 1 ? { ...msg, content: msg.content + parsed.content } : msg));
                  } else {
                    const newMessage: Message = { role: 'assistant', content: parsed.content, timestamp: new Date().toLocaleTimeString() };
                    return [...prev, newMessage];
                  }
                });
              } else if (parsed.tool_start) {
                const { tool_name, tool_use_id, content_block_index } = parsed.tool_start;
                const toolMessage: Message = {
                  role: 'assistant',
                  content: '',
                  tool_name,
                  tool_use_id,
                  content_block_index,
                  tool_is_active: true,
                  timestamp: new Date().toLocaleTimeString(),
                };
                setMessages((prev) => [...prev, toolMessage]);
                
                // Add to active tool calls
                setActiveToolCalls(prev => new Set(prev).add(tool_use_id || ''));
              } else if (parsed.tool_end) {
                const { tool_use_id, content_block_index } = parsed.tool_end;
                setMessages((prev) =>
                  prev.map((msg) => {
                    if (msg.tool_use_id === tool_use_id) {
                      return { ...msg, tool_is_active: false };
                    }
                    return msg;
                  })
                );
                
                // Remove from active tool calls
                setActiveToolCalls(prev => {
                  const newSet = new Set(prev);
                  newSet.delete(tool_use_id || '');
                  return newSet;
                });
                
                // Fetch updated to-do list when a tool call completes
                if (mode === 'agent') {
                  fetchTodoList();
                }
              }
            } catch (e) {
              console.warn('Failed to parse streaming data:', data);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error calling planner agent:', error);
      // Update the last message with error content
      setMessages((prev) =>
        prev.map((msg, index) => {
          if (index === prev.length - 1 && msg.role === 'assistant') {
            return { ...msg, content: 'Sorry, I encountered an error. Please make sure the backend server is running.' };
          }
          return msg;
        })
      );
    } finally {
      setIsLoading(false);
    }
  };

  const chatInputProps = {
    onSendMessage: handleSendMessage,
    disabled: isLoading,
    attachedFile: attachedFile,
    isProcessingFile: isProcessingFile,
    onFileAttach: handleFileAttach,
    onRemoveAttachment: handleRemoveAttachment,
    mode: mode,
    onModeChange: handleModeChange,
  };

  if (!hasStarted) {
    // Welcome page with centered ChatInput
    return (
      <div className="h-screen flex flex-col items-center justify-center relative" style={{backgroundColor: '#fdfdf1'}}>
        {/* Logo and title in top left */}
        <div className="absolute top-6 left-6 flex items-center gap-3">
          <img src="/scout-favicon.svg" alt="Scout" className="w-8 h-8" />
          <h1 className="text-2xl font-light text-gray-800">Scout</h1>
        </div>
        
        <div className="w-full max-w-2xl px-6">
          {/* Time-based greeting */}
          <div className="text-center mb-8">
            <p className="text-2xl text-gray-700 font-medium">{getTimeBasedGreeting()}</p>
          </div>
          
          <ChatInput {...chatInputProps} />
        </div>
      </div>
    );
  }

  // Chat mode with messages
  return (
    <div className="h-screen relative" style={{backgroundColor: '#fdfdf1'}}>
      {/* Logo and title in top left */}
      <div className="absolute top-6 left-6 flex items-center gap-3 z-30">
        <img src="/scout-favicon.svg" alt="Scout" className="w-6 h-6" />
        <h1 className="text-2xl font-light text-gray-800">Scout</h1>
      </div>
      
      <Sidebar onNewChat={startNewChat} />
      <ChatSection 
        messages={messages}
        isLoading={isLoading}
        onSendMessage={handleSendMessage}
        attachedFile={attachedFile}
        isProcessingFile={isProcessingFile}
        onFileAttach={handleFileAttach}
        onRemoveAttachment={handleRemoveAttachment}
        mode={mode}
        todoList={todoList}
        activeToolCalls={activeToolCalls}
      />
    </div>
  )
}

export default App;
