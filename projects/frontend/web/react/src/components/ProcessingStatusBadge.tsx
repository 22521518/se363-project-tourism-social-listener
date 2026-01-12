import { ProcessingStatus, ProcessingTask, TASK_LABELS, TASK_COLORS } from '../types/raw_data';
import { Check, X } from 'lucide-react';

interface ProcessingStatusBadgeProps {
  status: ProcessingStatus;
  compact?: boolean;
}

/**
 * Badge showing processing status for all 4 tasks
 */
export function ProcessingStatusBadge({ status, compact = false }: ProcessingStatusBadgeProps) {
  const tasks: ProcessingTask[] = ['asca', 'intention', 'location_extraction', 'traveling_type'];
  
  const processedCount = tasks.filter(t => status[t]).length;
  const allProcessed = processedCount === 4;
  const noneProcessed = processedCount === 0;

  if (compact) {
    return (
      <div 
        className={`
          inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium
          ${allProcessed ? 'bg-green-100 text-green-700' : 
            noneProcessed ? 'bg-gray-100 text-gray-600' : 
            'bg-amber-100 text-amber-700'}
        `}
      >
        {allProcessed ? (
          <>
            <Check className="w-3 h-3" />
            <span>Processed</span>
          </>
        ) : noneProcessed ? (
          <>
            <X className="w-3 h-3" />
            <span>Unprocessed</span>
          </>
        ) : (
          <span>{processedCount}/4 Tasks</span>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-1">
      {tasks.map(task => (
        <span
          key={task}
          className={`
            inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
            ${status[task] 
              ? 'bg-opacity-20' 
              : 'bg-gray-100 text-gray-400'}
          `}
          style={status[task] ? {
            backgroundColor: `${TASK_COLORS[task]}20`,
            color: TASK_COLORS[task],
          } : undefined}
        >
          {status[task] ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
          <span className="hidden sm:inline">{TASK_LABELS[task]}</span>
        </span>
      ))}
    </div>
  );
}

interface ProcessingStatusFilterProps {
  value: 'all' | 'processed' | 'unprocessed';
  onChange: (value: 'all' | 'processed' | 'unprocessed') => void;
  task?: ProcessingTask | 'all';
  onTaskChange?: (task: ProcessingTask | 'all') => void;
}

/**
 * Filter controls for processing status
 */
export function ProcessingStatusFilter({
  value,
  onChange,
  task = 'all',
  onTaskChange,
}: ProcessingStatusFilterProps) {
  const statusOptions = [
    { value: 'all' as const, label: 'All Data' },
    { value: 'processed' as const, label: 'Processed' },
    { value: 'unprocessed' as const, label: 'Unprocessed' },
  ];

  const taskOptions: { value: ProcessingTask | 'all'; label: string }[] = [
    { value: 'all', label: 'Any Task' },
    { value: 'asca', label: 'ASCA' },
    { value: 'intention', label: 'Intention' },
    { value: 'location_extraction', label: 'Location' },
    { value: 'traveling_type', label: 'Travel Type' },
  ];

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Status:</span>
        <div className="flex border border-gray-200 rounded overflow-hidden">
          {statusOptions.map(option => (
            <button
              key={option.value}
              onClick={() => onChange(option.value)}
              className={`
                px-3 py-1 text-sm transition-colors
                ${value === option.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'}
              `}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {onTaskChange && value !== 'all' && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Task:</span>
          <select
            value={task}
            onChange={(e) => onTaskChange(e.target.value as ProcessingTask | 'all')}
            className="px-3 py-1 text-sm border border-gray-200 rounded bg-white"
          >
            {taskOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
