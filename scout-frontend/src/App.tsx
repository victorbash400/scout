import { useState } from 'react'
import './App.css'
import ChatSection from './chat/chatsection'
import ChatInput from './chat/chatinput'
import Sidebar from './components/sidebar'
import { getTimeBasedGreeting } from './data/greetings'

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tool_name?: string;
  tool_use_id?: string;
  content_block_index?: number;
  tool_is_active?: boolean;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  const uploadFile = async (file: File) => {
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
      console.log('File uploaded successfully:', result.file_path);
      return result.file_path;
    } catch (error) {
      console.error('Error uploading file:', error);
      // Optionally, update the UI to show an error message
      return null;
    }
  };

  const handleSendMessage = async (content: string, file?: File) => {
    setHasStarted(true);
    setIsLoading(true);

    let fileInfo = '';
    if (file) {
      const uploadedFilePath = await uploadFile(file);
      if (uploadedFilePath) {
        fileInfo = `(Attached file: ${file.name}) `;
      }
    }

    const messageToSend = `${fileInfo}${content}`.trim();

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: messageToSend,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMessage]);

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
        body: JSON.stringify({ message: messageToSend }),
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
          
          <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
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
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  )
}

export default App
