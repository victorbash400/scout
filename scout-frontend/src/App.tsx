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
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  const handleSendMessage = (content: string) => {
    // Add user message
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setHasStarted(true);

    // Simulate AI response after a delay
    setTimeout(() => {
      const aiMessage: Message = {
        role: 'assistant',
        content: `I received your message: "${content}". This is a demo response from the AI assistant.`,
        timestamp: new Date().toLocaleTimeString()
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1500);
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
