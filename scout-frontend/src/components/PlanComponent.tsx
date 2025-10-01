import React, { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle2 } from 'lucide-react';
import ReportLink from './ReportLink';

interface TodoList {
  competition_tasks: string[];
  market_tasks: string[];
  price_tasks: string[];
  legal_tasks: string[];
}

interface CategoryProps {
  title: string;
  tasks: string[];
  defaultExpanded?: boolean;
}

const Category: React.FC<CategoryProps> = ({ title, tasks, defaultExpanded = false }) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  if (!Array.isArray(tasks) || tasks.length === 0) return null;

  return (
    <div className="mb-3">
      <button
        className="flex items-center justify-between w-full p-2 text-left rounded-lg hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-700 text-sm">{title}</span>
          <span className="text-xs bg-gray-100 text-gray-500 rounded-full px-1.5 py-0.5">
            {tasks.length}
          </span>
        </div>
        {isExpanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
      </button>
      
      {isExpanded && (
        <div className="ml-6 mt-1 space-y-1">
          {tasks.map((task, index) => (
            <div key={index} className="flex items-start gap-2 p-1.5 rounded hover:bg-gray-50">
              <CheckCircle2 className="w-4 h-4 text-gray-600 mt-0.5 flex-shrink-0" />
              <span className="text-sm text-gray-600">{task}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

interface PlanComponentProps {
  todoList: TodoList | null;
  generatedReports?: { name: string; path: string }[];
}

const PlanComponent: React.FC<PlanComponentProps> = ({ todoList, generatedReports = [] }) => {
  const hasTasks = todoList && Object.values(todoList).some(category => category.length > 0);
  const hasReports = generatedReports && generatedReports.length > 0;

  return (
    <div className="flex flex-col bg-white rounded-xl max-h-[80vh]">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-md font-semibold text-gray-800">Research Plan</h2>
        <p className="text-xs text-gray-500 mt-1">Tasks for specialist agents</p>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        {hasTasks ? (
          <div className="space-y-1">
            <Category 
              title="Competition Analysis" 
              tasks={todoList.competition_tasks} 
              defaultExpanded={true}
            />
            <Category 
              title="Market Research" 
              tasks={todoList.market_tasks} 
            />
            <Category 
              title="Price Analysis" 
              tasks={todoList.price_tasks} 
            />
            <Category 
              title="Legal & Regulatory" 
              tasks={todoList.legal_tasks} 
            />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="w-6 h-6 border-2 border-green-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
      </div>
      
      {hasReports && (
        <div className="p-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Generated Reports</h3>
          <div className="space-y-2">
            {generatedReports.map(report => (
              <ReportLink key={report.path} report={report} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlanComponent;