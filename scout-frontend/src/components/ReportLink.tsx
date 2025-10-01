
import React from 'react';
import { FileDown, FileText } from 'lucide-react';

interface ReportLinkProps {
  report: {
    name: string;
    path: string;
  };
  className?: string;
}

const ReportLink: React.FC<ReportLinkProps> = ({ report, className = "" }) => {
  const handleDownload = () => {
    const reportFilename = report.path.split('/').pop();
    window.open(`http://localhost:8000/api/reports/${reportFilename}`, '_blank');
  };

  return (
    <button
      type="button"
      onClick={handleDownload}
      title={report.name}
      className={`flex items-center bg-green-50 border border-green-700 rounded-md px-2 py-1 text-xs transition-all duration-300 cursor-pointer max-w-[160px] focus:outline-none focus:ring-2 focus:ring-green-700 hover:bg-green-100 hover:shadow-md hover:border-green-900 ${className}`}

    >
      <FileText className="w-4 h-4 text-green-700 flex-shrink-0 mr-1" />
      <span
        className="text-green-800 font-medium truncate transition-all duration-300"
        style={{ minWidth: 0, maxWidth: '100%' }}
      >
        {report.name}
      </span>
      <FileDown className="w-4 h-4 ml-1 text-green-700 hover:text-green-900 flex-shrink-0" />
    </button>
  );
};

export default ReportLink;
