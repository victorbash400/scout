import React, { useState } from 'react';
import { Plus, FolderOpen } from 'lucide-react';

const Sidebar: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div 
      className="fixed left-4 bottom-8 z-40 transition-all duration-300 ease-in-out"
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <div 
        className="rounded-2xl shadow-lg transition-all duration-300 ease-in-out"
        style={{backgroundColor: '#04331c'}}
      >
        <div className={`flex flex-col items-center py-4 transition-all duration-300 ease-in-out ${
          isExpanded ? 'px-6' : 'px-4'
        }`}>
          {/* New Chat */}
          <button 
            className={`flex items-center gap-3 text-white hover:bg-black hover:bg-opacity-20 rounded-xl transition-all duration-200 p-3 w-full ${
              isExpanded ? 'justify-start' : 'justify-center'
            }`}
            title="New Chat"
          >
            <Plus className="w-5 h-5 flex-shrink-0" />
            {isExpanded && (
              <span className="text-sm font-medium whitespace-nowrap">New Chat</span>
            )}
          </button>

          {/* Projects */}
          <button 
            className={`flex items-center gap-3 text-white hover:bg-black hover:bg-opacity-20 rounded-xl transition-all duration-200 p-3 w-full mt-2 ${
              isExpanded ? 'justify-start' : 'justify-center'
            }`}
            title="Projects"
          >
            <FolderOpen className="w-5 h-5 flex-shrink-0" />
            {isExpanded && (
              <span className="text-sm font-medium whitespace-nowrap">Projects</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
