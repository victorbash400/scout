import { useState } from 'react';
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

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  // New state for file handling
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const [fileContext, setFileContext] = useState<string | null>(null);

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
        body: JSON.stringify({ message: content }),
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
              } else if (parsed.tool_end) {
                const { content_block_index } = parsed.tool_end;
                setMessages((prev) =>
                  prev.map((msg) => {
                    if (msg.content_block_index === content_block_index) {
                      return { ...msg, tool_is_active: false };
                    }
                    return msg;
                  })
                );
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
      
      <Sidebar />
      <ChatSection 
        messages={messages}
        isLoading={isLoading}
        onSendMessage={handleSendMessage}
        attachedFile={attachedFile}
        isProcessingFile={isProcessingFile}
        onFileAttach={handleFileAttach}
        onRemoveAttachment={handleRemoveAttachment}
      />
    </div>
  )
}

export default App;
