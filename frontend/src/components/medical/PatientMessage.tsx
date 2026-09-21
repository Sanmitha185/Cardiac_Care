import React from 'react';
import { User } from 'lucide-react';

interface PatientMessageProps {
  content: string;
  timestamp?: string;
}

export const PatientMessage: React.FC<PatientMessageProps> = ({
  content,
  timestamp,
}) => {
  return (
    <div className="flex items-start justify-end space-x-3 max-w-2xl ml-auto my-3">
      <div className="flex-1 flex flex-col items-end">
        <div className="flex items-center space-x-2 mb-1">
          {timestamp && (
            <span className="text-[10px] text-slate-400">
              {timestamp}
            </span>
          )}
          <span className="text-xs font-bold text-slate-600 tracking-wide">
            Patient
          </span>
        </div>

        {/* Message bubble */}
        <div className="bg-slate-900 text-white rounded-2xl rounded-tr-sm px-5 py-3.5 text-sm sm:text-base leading-relaxed shadow-sm max-w-lg">
          {content}
        </div>
      </div>

      {/* Patient Avatar */}
      <div className="w-9 h-9 rounded-xl bg-slate-200 text-slate-700 flex items-center justify-center flex-shrink-0 mt-0.5">
        <User className="w-5 h-5" />
      </div>
    </div>
  );
};
