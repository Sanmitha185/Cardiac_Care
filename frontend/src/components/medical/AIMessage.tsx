import React from 'react';
import { Stethoscope } from 'lucide-react';

interface AIMessageProps {
  content: string;
  timestamp?: string;
  isLatest?: boolean;
}

export const AIMessage: React.FC<AIMessageProps> = ({
  content,
  timestamp,
  isLatest = false,
}) => {
  return (
    <div className="flex items-start space-x-3 max-w-2xl my-3">
      {/* Dr. Cardia Clinical Avatar */}
      <div className="w-10 h-10 rounded-xl bg-brand-700 text-white flex items-center justify-center shadow-md shadow-brand-700/20 flex-shrink-0 mt-0.5">
        <Stethoscope className="w-5 h-5" />
      </div>

      <div className="flex-1">
        <div className="flex items-baseline space-x-2 mb-1">
          <span className="text-xs font-bold text-slate-900 tracking-wide">
            Dr. Cardia
          </span>
          <span className="text-[10px] text-brand-700 font-medium">
            AI Cardiac Care Assistant
          </span>
          {timestamp && (
            <span className="text-[10px] text-slate-400">
              • {timestamp}
            </span>
          )}
        </div>

        {/* Message bubble */}
        <div className={`bg-brand-50/90 border border-brand-100/90 rounded-2xl rounded-tl-sm px-5 py-3.5 text-slate-900 text-sm sm:text-base leading-relaxed shadow-xs ${
          isLatest ? 'ring-2 ring-brand-400/30' : ''
        }`}>
          {content}
        </div>
      </div>
    </div>
  );
};
