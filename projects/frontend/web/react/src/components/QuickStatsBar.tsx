import {
  Video,
  MessageCircle,
  CheckCircle2,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';

interface QuickStatsBarProps {
  totalVideos: number;
  totalComments?: number;
  totalProcessed?: number;
  positiveCount?: number;
  negativeCount?: number;
}

/**
 * Quick stats bar showing aggregate counts
 */
export function QuickStatsBar({
  totalVideos,
  totalComments = 0,
  totalProcessed = 0,
  positiveCount = 0,
  negativeCount = 0,
}: QuickStatsBarProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Video className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="text-2xl font-semibold text-gray-900">
              {totalVideos.toLocaleString()}
            </p>
            <p className="text-sm text-gray-600">Videos</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <MessageCircle className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <p className="text-2xl font-semibold text-gray-900">
              {totalComments.toLocaleString()}
            </p>
            <p className="text-sm text-gray-600">Comments</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-semibold text-gray-900">
              {totalProcessed.toLocaleString()}
            </p>
            <p className="text-sm text-gray-600">Processed</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <ThumbsUp className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-semibold text-green-600">
              {positiveCount.toLocaleString()}
            </p>
            <p className="text-sm text-gray-600">Positive</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-100 rounded-lg">
            <ThumbsDown className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p className="text-2xl font-semibold text-red-600">
              {negativeCount.toLocaleString()}
            </p>
            <p className="text-sm text-gray-600">Negative</p>
          </div>
        </div>
      </div>
    </div>
  );
}
