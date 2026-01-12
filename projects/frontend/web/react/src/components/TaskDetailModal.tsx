import { X, CheckCircle2, AlertCircle, MapPin, Target, Plane, MessageCircle, Loader2 } from 'lucide-react';
import { RawDataItem, ProcessingTask, TASK_LABELS, TASK_COLORS, YouTubeCommentMetadata, WebCrawlMetadata } from '../types/raw_data';
import { useEffect, useState } from 'react';
import { fetchApi } from '../services/api';

interface TaskDetailModalProps {
  item: RawDataItem | null;
  onClose: () => void;
}

interface TaskDetails {
  asca: {
    processed: boolean;
    aspects: Array<{ category: string; sentiment: string; score?: number }>;
  };
  intention: {
    processed: boolean;
    intention: string | null;
    confidence?: number;
  };
  location_extraction: {
    processed: boolean;
    locations: Array<{ name: string; type: string; score?: number }>;
  };
  traveling_type: {
    processed: boolean;
    type: string | null;
    confidence?: number;
  };
}

/**
 * Modal component for displaying detailed task processing results
 */
export function TaskDetailModal({ item, onClose }: TaskDetailModalProps) {
  const [details, setDetails] = useState<TaskDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!item) {
      setDetails(null);
      return;
    }

    const fetchDetails = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetchApi<{
          asca: { processed: boolean; aspects: Array<{ category: string; sentiment: string; confidence: number }> };
          intention: { processed: boolean; intention_type: string | null };
          location_extraction: { processed: boolean; locations: Array<{ word: string; entity_group: string; score: number }> };
          traveling_type: { processed: boolean; traveling_type: string | null };
        }>(`/raw_data/${item.id}/processing`);

        setDetails({
          asca: {
            processed: response.asca?.processed || false,
            aspects: (response.asca?.aspects || []).map(a => ({
              category: a.category,
              sentiment: a.sentiment,
              score: a.confidence,
            })),
          },
          intention: {
            processed: response.intention?.processed || false,
            intention: response.intention?.intention_type || null,
            confidence: undefined,
          },
          location_extraction: {
            processed: response.location_extraction?.processed || false,
            locations: (response.location_extraction?.locations || []).map(l => ({
              name: l.word,
              type: l.entity_group,
              score: l.score,
            })),
          },
          traveling_type: {
            processed: response.traveling_type?.processed || false,
            type: response.traveling_type?.traveling_type || null,
            confidence: undefined,
          },
        });
      } catch (err) {
        console.error('Error fetching processing details:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch details');
        // Fallback to status-only display
        setDetails({
          asca: { processed: item.processing_status.asca, aspects: [] },
          intention: { processed: item.processing_status.intention, intention: null },
          location_extraction: { processed: item.processing_status.location_extraction, locations: [] },
          traveling_type: { processed: item.processing_status.traveling_type, type: null },
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [item]);

  if (!item) return null;

  const isYouTube = item.source_type === 'youtube_comment';
  const metadata = item.metadata;

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }} className="z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
        className="bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div style={{ width: '700px', maxHeight: '500px' }} className="relative bg-white rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-blue-600" />
            <h2 className="font-semibold text-gray-900">Chi tiết xử lý</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          {/* Source Info */}
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">
              {isYouTube ? 'YouTube Comment' : 'Web Crawl'}
            </div>
            <p className="text-sm text-gray-800">{item.text || '(No content)'}</p>
            <div className="flex flex-wrap gap-2 mt-2 text-xs text-gray-500">
              {isYouTube ? (
                <>
                  <span>👤 {(metadata as YouTubeCommentMetadata).author_name || 'Anonymous'}</span>
                  <span>📹 {(metadata as YouTubeCommentMetadata).video_title}</span>
                </>
              ) : (
                <>
                  <span>🌐 {(metadata as WebCrawlMetadata).url}</span>
                </>
              )}
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              <span className="ml-2 text-gray-600">Đang tải chi tiết xử lý...</span>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              ⚠️ {error}
            </div>
          )}

          {/* Task Cards */}
          {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* ASCA - Detailed Analysis */}
            <TaskCard
              task="asca"
              processed={item.processing_status.asca}
              title="ASCA Analysis"
              icon={<Target className="w-4 h-4" />}
              fullWidth={true}
            >
              {details?.asca.aspects && details.asca.aspects.length > 0 ? (
                <div className="space-y-3">
                  {/* Summary Stats */}
                  <div className="flex gap-4 text-xs pb-2 border-b border-gray-200">
                    <div className="flex items-center gap-1">
                      <span className="inline-block w-2 h-2 rounded-full bg-green-500"></span>
                      <span className="text-gray-600">
                        Positive: {details.asca.aspects.filter(a => a.sentiment === 'positive').length}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="inline-block w-2 h-2 rounded-full bg-red-500"></span>
                      <span className="text-gray-600">
                        Negative: {details.asca.aspects.filter(a => a.sentiment === 'negative').length}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="inline-block w-2 h-2 rounded-full bg-gray-400"></span>
                      <span className="text-gray-600">
                        Neutral: {details.asca.aspects.filter(a => a.sentiment === 'neutral').length}
                      </span>
                    </div>
                  </div>

                  {/* Detailed Aspect List */}
                  <div className="space-y-2">
                    {details.asca.aspects.map((aspect, i) => (
                      <div 
                        key={i} 
                        className={`p-2 rounded-lg border ${
                          aspect.sentiment === 'positive' ? 'bg-green-50 border-green-200' :
                          aspect.sentiment === 'negative' ? 'bg-red-50 border-red-200' :
                          'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className={`text-sm font-medium ${
                              aspect.sentiment === 'positive' ? 'text-green-800' :
                              aspect.sentiment === 'negative' ? 'text-red-800' :
                              'text-gray-800'
                            }`}>
                              {aspect.sentiment === 'positive' ? '👍' : aspect.sentiment === 'negative' ? '👎' : '😐'}
                              {' '}{aspect.category}
                            </span>
                          </div>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            aspect.sentiment === 'positive' ? 'bg-green-200 text-green-800' :
                            aspect.sentiment === 'negative' ? 'bg-red-200 text-red-800' :
                            'bg-gray-200 text-gray-800'
                          }`}>
                            {aspect.sentiment}
                          </span>
                        </div>
                        
                        {/* Confidence Score Bar */}
                        {aspect.score !== undefined && (
                          <div className="mt-2">
                            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                              <span>Confidence</span>
                              <span>{(aspect.score * 100).toFixed(1)}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-1.5">
                              <div 
                                className={`h-1.5 rounded-full ${
                                  aspect.sentiment === 'positive' ? 'bg-green-500' :
                                  aspect.sentiment === 'negative' ? 'bg-red-500' :
                                  'bg-gray-500'
                                }`}
                                style={{ width: `${Math.min(aspect.score * 100, 100)}%` }}
                              ></div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500 italic">
                  Không có aspect nào được phát hiện
                </div>
              )}
            </TaskCard>

            {/* Intention */}
            <TaskCard
              task="intention"
              processed={item.processing_status.intention}
              title="Intention"
              icon={<Target className="w-4 h-4" />}
            >
              {details?.intention.intention ? (
                <div className="text-sm font-medium text-purple-700">
                  🎯 {details.intention.intention}
                </div>
              ) : null}
            </TaskCard>

            {/* Location */}
            <TaskCard
              task="location_extraction"
              processed={item.processing_status.location_extraction}
              title="Location"
              icon={<MapPin className="w-4 h-4" />}
            >
              {details?.location_extraction.locations && details.location_extraction.locations.length > 0 ? (
                <div className="flex flex-wrap gap-1">
                  {details.location_extraction.locations.map((loc, i) => (
                    <span key={i} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                      📍 {loc.name} ({loc.type})
                    </span>
                  ))}
                </div>
              ) : null}
            </TaskCard>

            {/* Traveling Type */}
            <TaskCard
              task="traveling_type"
              processed={item.processing_status.traveling_type}
              title="Traveling Type"
              icon={<Plane className="w-4 h-4" />}
            >
              {details?.traveling_type.type ? (
                <div className="text-sm font-medium text-amber-700">
                  ✈️ {details.traveling_type.type}
                </div>
              ) : null}
            </TaskCard>
          </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 px-4 py-3 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Individual task card component
 */
function TaskCard({ 
  task, 
  processed, 
  title, 
  icon, 
  children,
  fullWidth = false,
}: { 
  task: ProcessingTask;
  processed: boolean;
  title: string;
  icon: React.ReactNode;
  children?: React.ReactNode;
  fullWidth?: boolean;
}) {
  return (
    <div className={`p-3 rounded-lg border ${
      processed 
        ? 'bg-green-50 border-green-200' 
        : 'bg-amber-50 border-amber-200'
    } ${fullWidth ? 'md:col-span-2' : ''}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-gray-600">{icon}</span>
          <span className="font-medium text-sm text-gray-900">{title}</span>
        </div>
        {processed ? (
          <CheckCircle2 className="w-4 h-4 text-green-600" />
        ) : (
          <AlertCircle className="w-4 h-4 text-amber-600" />
        )}
      </div>
      
      {processed ? (
        children || <span className="text-sm text-gray-600">Đã xử lý</span>
      ) : (
        <div className="text-sm text-amber-700 italic">
          ⚠️ Chưa xác định - Cần được xử lý
        </div>
      )}
    </div>
  );
}
