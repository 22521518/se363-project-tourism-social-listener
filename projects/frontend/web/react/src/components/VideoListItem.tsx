import { useState, useEffect } from 'react';
import {
  Play,
  MessageCircle,
  CheckCircle2,
  ThumbsUp,
  ThumbsDown,
  Minus,
  MapPin,
  Target,
  Plane,
  ChevronDown,
  ChevronUp,
  Eye,
  Calendar,
  Loader2,
  X,
  AlertCircle,
} from 'lucide-react';
import {
  YouTubeVideoWithStats,
  YouTubeCommentWithStats,
  SENTIMENT_COLORS,
  SENTIMENT_BG,
  INTENTION_COLORS,
  TRAVEL_TYPE_COLORS,
} from '../types/video_with_stats';
import { useCommentsWithStats } from '../hooks/useCommentsWithStats';

interface VideoListItemProps {
  video: YouTubeVideoWithStats;
}

/**
 * Video list item with processing stats summary and expandable comments
 */
export function VideoListItem({ video }: VideoListItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const { stats } = video;

  // Calculate sentiment percentage
  const totalSentiment = stats.sentiment.positive + stats.sentiment.negative + stats.sentiment.neutral;
  const positivePercent = totalSentiment > 0 ? Math.round((stats.sentiment.positive / totalSentiment) * 100) : 0;
  const negativePercent = totalSentiment > 0 ? Math.round((stats.sentiment.negative / totalSentiment) * 100) : 0;

  return (
    <>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {/* Video Header - Clickable */}
        <div 
          className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={() => setShowDetailModal(true)}
        >
          <div className="flex gap-4">
            {/* Thumbnail */}
            <div className="flex-shrink-0">
              {video.thumbnail_url ? (
                <img
                  src={video.thumbnail_url}
                  alt={video.title}
                  className="w-40 h-24 object-cover rounded-lg"
                />
              ) : (
                <div className="w-40 h-24 bg-gray-200 rounded-lg flex items-center justify-center">
                  <Play className="w-8 h-8 text-gray-400" />
                </div>
              )}
            </div>

            {/* Video Info */}
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-gray-900 line-clamp-2 mb-1">{video.title}</h3>
              <div className="flex items-center gap-3 text-sm text-gray-600 mb-2">
                <span className="font-medium">{video.channel.title}</span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {new Date(video.published_at).toLocaleDateString('vi-VN')}
                </span>
                {video.view_count && (
                  <span className="flex items-center gap-1">
                    <Eye className="w-3 h-3" />
                    {video.view_count.toLocaleString()}
                  </span>
                )}
              </div>

              {/* Processing Stats Summary */}
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <div className="flex items-center gap-1 text-gray-600">
                  <MessageCircle className="w-4 h-4" />
                  <span>{stats.total_comments} comments</span>
                </div>
                <div className="flex items-center gap-1 text-green-600">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{stats.processed_count} processed</span>
                </div>
                
                {/* Sentiment Summary */}
                {totalSentiment > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1 text-green-600">
                      <ThumbsUp className="w-3 h-3" /> {positivePercent}%
                    </span>
                    <span className="flex items-center gap-1 text-red-600">
                      <ThumbsDown className="w-3 h-3" /> {negativePercent}%
                    </span>
                  </div>
                )}

                {/* Click hint */}
                <span className="text-xs text-gray-400 ml-auto">Click để xem chi tiết</span>
              </div>
            </div>
          </div>

          {/* Quick Stats Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
            {/* Top Locations */}
            {stats.top_locations.length > 0 && (
              <div className="p-2 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-1 text-xs text-blue-600 mb-1">
                  <MapPin className="w-3 h-3" /> Top Locations
                </div>
                <div className="flex flex-wrap gap-1">
                  {stats.top_locations.slice(0, 3).map((loc, i) => (
                    <span key={i} className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                      {loc.name} ({loc.count})
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Top Intentions */}
            {stats.top_intentions.length > 0 && (
              <div className="p-2 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-1 text-xs text-purple-600 mb-1">
                  <Target className="w-3 h-3" /> Intentions
                </div>
                <div className="flex flex-wrap gap-1">
                  {stats.top_intentions.slice(0, 2).map((item, i) => (
                    <span
                      key={i}
                      className="text-xs px-1.5 py-0.5 rounded"
                      style={{
                        backgroundColor: `${INTENTION_COLORS[item.name] || '#6b7280'}20`,
                        color: INTENTION_COLORS[item.name] || '#6b7280',
                      }}
                    >
                      {item.name} ({item.count})
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Top Travel Types */}
            {stats.top_travel_types.length > 0 && (
              <div className="p-2 bg-green-50 rounded-lg">
                <div className="flex items-center gap-1 text-xs text-green-600 mb-1">
                  <Plane className="w-3 h-3" /> Travel Types
                </div>
                <div className="flex flex-wrap gap-1">
                  {stats.top_travel_types.slice(0, 2).map((item, i) => (
                    <span
                      key={i}
                      className="text-xs px-1.5 py-0.5 rounded"
                      style={{
                        backgroundColor: `${TRAVEL_TYPE_COLORS[item.name] || '#6b7280'}20`,
                        color: TRAVEL_TYPE_COLORS[item.name] || '#6b7280',
                      }}
                    >
                      {item.name} ({item.count})
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Sentiment Breakdown */}
            {totalSentiment > 0 && (
              <div className="p-2 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-600 mb-1">Sentiment</div>
                <div className="flex h-2 rounded-full overflow-hidden bg-gray-200">
                  <div
                    className="bg-green-500"
                    style={{ width: `${positivePercent}%` }}
                  />
                  <div
                    className="bg-red-500"
                    style={{ width: `${negativePercent}%` }}
                  />
                  <div
                    className="bg-gray-400"
                    style={{ width: `${100 - positivePercent - negativePercent}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>👍 {stats.sentiment.positive}</span>
                  <span>👎 {stats.sentiment.negative}</span>
                  <span>😐 {stats.sentiment.neutral}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Expand/Collapse Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-4 py-2 flex items-center justify-center gap-2 text-blue-600 hover:bg-blue-50 transition-colors text-sm border-t border-gray-100"
        >
          {isExpanded ? 'Hide Comments' : 'Show Comments'}
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {/* Expanded Comments */}
        {isExpanded && <CommentsSection videoId={video.id} />}
      </div>

      {/* Video Detail Modal */}
      {showDetailModal && (
        <VideoDetailModal video={video} onClose={() => setShowDetailModal(false)} />
      )}
    </>
  );
}

/**
 * Modal for displaying detailed video processing stats
 */
function VideoDetailModal({
  video,
  onClose,
}: {
  video: YouTubeVideoWithStats;
  onClose: () => void;
}) {
  const { stats } = video;
  const totalSentiment = stats.sentiment.positive + stats.sentiment.negative + stats.sentiment.neutral;
  const positivePercent = totalSentiment > 0 ? Math.round((stats.sentiment.positive / totalSentiment) * 100) : 0;
  const negativePercent = totalSentiment > 0 ? Math.round((stats.sentiment.negative / totalSentiment) * 100) : 0;
  const neutralPercent = 100 - positivePercent - negativePercent;

  return (
    <div
      style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}
      className="z-50 flex items-center justify-center"
    >

      {/* Modal */}
      <div style={{ width: '70vw', height: '70vh' }} className="relative bg-white rounded-xl shadow-2xl overflow-hidden flex-col mx-12 my-12">
        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center gap-2">
            <Play className="w-5 h-5 text-blue-600" />
            <h2 className="font-semibold text-gray-900">Thống kê xử lý Video</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-4 min-h-max max-h-max overflow-y-auto">
          {/* Video Info */}
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex gap-4">
              {video.thumbnail_url && (
                <img
                  src={video.thumbnail_url}
                  alt={video.title}
                  className="w-32 h-20 object-cover rounded-lg"
                />
              )}
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-gray-900 line-clamp-2 mb-1">{video.title}</h3>
                <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                  <span>📺 {video.channel.title}</span>
                  <span>📅 {new Date(video.published_at).toLocaleDateString('vi-VN')}</span>
                  {video.view_count && <span>👁 {video.view_count.toLocaleString()} views</span>}
                  {video.like_count && <span>👍 {video.like_count.toLocaleString()} likes</span>}
                </div>
              </div>
            </div>
          </div>

          {/* Processing Overview */}
          <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">📊 Tổng quan xử lý</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{stats.total_comments}</div>
                <div className="text-xs text-gray-500">Tổng comments</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.processed_count}</div>
                <div className="text-xs text-gray-500">Đã xử lý</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {stats.total_comments > 0 ? Math.round((stats.processed_count / stats.total_comments) * 100) : 0}%
                </div>
                <div className="text-xs text-gray-500">Tỷ lệ hoàn thành</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{stats.asca_categories.length}</div>
                <div className="text-xs text-gray-500">ASCA Categories</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Sentiment Breakdown */}
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <ThumbsUp className="w-4 h-4" /> Phân tích Sentiment
              </h4>
              {totalSentiment > 0 ? (
                <>
                  <div className="flex h-4 rounded-full overflow-hidden bg-gray-200 mb-3">
                    <div className="bg-green-500" style={{ width: `${positivePercent}%` }} />
                    <div className="bg-red-500" style={{ width: `${negativePercent}%` }} />
                    <div className="bg-gray-400" style={{ width: `${neutralPercent}%` }} />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">👍 Tích cực</span>
                      <span className="font-medium text-green-600">{stats.sentiment.positive} ({positivePercent}%)</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">👎 Tiêu cực</span>
                      <span className="font-medium text-red-600">{stats.sentiment.negative} ({negativePercent}%)</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">😐 Trung lập</span>
                      <span className="font-medium text-gray-600">{stats.sentiment.neutral} ({neutralPercent}%)</span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-sm text-gray-500 italic text-center py-4">
                  Chưa có dữ liệu sentiment
                </div>
              )}
            </div>

            {/* Top Intentions */}
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <Target className="w-4 h-4" /> Top Intentions
              </h4>
              {stats.top_intentions.length > 0 ? (
                <div className="space-y-2">
                  {stats.top_intentions.map((item, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span
                        className="text-sm px-2 py-0.5 rounded"
                        style={{
                          backgroundColor: `${INTENTION_COLORS[item.name] || '#6b7280'}20`,
                          color: INTENTION_COLORS[item.name] || '#6b7280',
                        }}
                      >
                        🎯 {item.name}
                      </span>
                      <span className="font-medium text-gray-900">{item.count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500 italic text-center py-4">
                  Chưa có dữ liệu intention
                </div>
              )}
            </div>

            {/* Top Travel Types */}
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <Plane className="w-4 h-4" /> Top Travel Types
              </h4>
              {stats.top_travel_types.length > 0 ? (
                <div className="space-y-2">
                  {stats.top_travel_types.map((item, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span
                        className="text-sm px-2 py-0.5 rounded"
                        style={{
                          backgroundColor: `${TRAVEL_TYPE_COLORS[item.name] || '#6b7280'}20`,
                          color: TRAVEL_TYPE_COLORS[item.name] || '#6b7280',
                        }}
                      >
                        ✈️ {item.name}
                      </span>
                      <span className="font-medium text-gray-900">{item.count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500 italic text-center py-4">
                  Chưa có dữ liệu travel type
                </div>
              )}
            </div>

            {/* Top Locations */}
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <MapPin className="w-4 h-4" /> Top Locations
              </h4>
              {stats.top_locations.length > 0 ? (
                <div className="space-y-2">
                  {stats.top_locations.map((loc, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className="text-sm px-2 py-0.5 rounded bg-blue-100 text-blue-700">
                        📍 {loc.name}
                      </span>
                      <span className="font-medium text-gray-900">{loc.count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500 italic text-center py-4">
                  Chưa có dữ liệu location
                </div>
              )}
            </div>
          </div>

          {/* ASCA Categories Breakdown */}
          {stats.asca_categories.length > 0 && (
            <div className="mt-4 p-4 bg-white border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <Target className="w-4 h-4" /> ASCA Categories Breakdown
              </h4>
              <div className="space-y-3">
                {stats.asca_categories.map((cat, i) => {
                  const total = cat.positive + cat.negative + cat.neutral;
                  const posPercent = total > 0 ? Math.round((cat.positive / total) * 100) : 0;
                  const negPercent = total > 0 ? Math.round((cat.negative / total) * 100) : 0;
                  return (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-900">{cat.category}</span>
                        <span className="text-xs text-gray-500">Total: {total}</span>
                      </div>
                      <div className="flex h-2 rounded-full overflow-hidden bg-gray-200 mb-2">
                        <div className="bg-green-500" style={{ width: `${posPercent}%` }} />
                        <div className="bg-red-500" style={{ width: `${negPercent}%` }} />
                        <div className="bg-gray-400" style={{ width: `${100 - posPercent - negPercent}%` }} />
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-green-600">👍 {cat.positive}</span>
                        <span className="text-red-600">👎 {cat.negative}</span>
                        <span className="text-gray-600">😐 {cat.neutral}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
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
      
      {/* Backdrop */}
      <div
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
        className="-z-40 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
    </div>
  );
}

/**
 * Comments section with processing badges
 */
function CommentsSection({ videoId }: { videoId: string }) {
  const { data, meta, loading, error, fetch, fetchMore } = useCommentsWithStats(videoId);

  // Fetch on mount
  useEffect(() => {
    fetch();
  }, []);

  if (loading && data.length === 0) {
    return (
      <div className="p-4 border-t border-gray-100 flex items-center justify-center">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading comments...</span>
      </div>
    );
  }

  if (error && data.length === 0) {
    return (
      <div className="p-4 border-t border-gray-100 text-center text-gray-500">
        Failed to load comments
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="p-4 border-t border-gray-100 text-center text-gray-500">
        No processed comments available
      </div>
    );
  }

  return (
    <div className="border-t border-gray-100">
      <div className="divide-y divide-gray-100">
        {data.map((comment) => (
          <CommentItem key={comment.id} comment={comment} />
        ))}
      </div>

      {meta.hasMore && (
        <button
          onClick={fetchMore}
          disabled={loading}
          className="w-full px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 disabled:opacity-50"
        >
          {loading ? 'Loading...' : `Load more (${meta.total - data.length} remaining)`}
        </button>
      )}
    </div>
  );
}

/**
 * Individual comment with processing badges - clickable to show details
 */
function CommentItem({ comment }: { comment: YouTubeCommentWithStats }) {
  const [showModal, setShowModal] = useState(false);
  const { processing } = comment;

  return (
    <>
      <div 
        className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
        onClick={() => setShowModal(true)}
      >
        <div className="flex justify-between items-start gap-2 mb-2">
          <span className="text-sm font-medium text-gray-700">
            {comment.author_name || 'Anonymous'}
          </span>
          <span className="text-xs text-gray-500">
            {new Date(comment.published_at).toLocaleDateString('vi-VN')}
          </span>
        </div>

        <p className="text-sm text-gray-800 mb-2 line-clamp-3">{comment.text}</p>

        {/* Processing Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Sentiment */}
          {processing.sentiment && (
            <span
              className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full"
              style={{
                backgroundColor: SENTIMENT_BG[processing.sentiment],
                color: SENTIMENT_COLORS[processing.sentiment],
              }}
            >
              {processing.sentiment === 'positive' && <ThumbsUp className="w-3 h-3" />}
              {processing.sentiment === 'negative' && <ThumbsDown className="w-3 h-3" />}
              {processing.sentiment === 'neutral' && <Minus className="w-3 h-3" />}
              {processing.sentiment}
            </span>
          )}

          {/* Intention */}
          {processing.intention && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{
                backgroundColor: `${INTENTION_COLORS[processing.intention] || '#6b7280'}20`,
                color: INTENTION_COLORS[processing.intention] || '#6b7280',
              }}
            >
              🎯 {processing.intention}
            </span>
          )}

          {/* Travel Type */}
          {processing.travel_type && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{
                backgroundColor: `${TRAVEL_TYPE_COLORS[processing.travel_type] || '#6b7280'}20`,
                color: TRAVEL_TYPE_COLORS[processing.travel_type] || '#6b7280',
              }}
            >
              ✈️ {processing.travel_type}
            </span>
          )}

          {/* Locations */}
          {processing.locations.length > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
              📍 {processing.locations.slice(0, 2).join(', ')}
            </span>
          )}

          {/* Click hint */}
          <span className="text-xs text-gray-400 ml-auto">Click để xem chi tiết</span>
        </div>
      </div>

      {/* Detail Modal */}
      {showModal && (
        <CommentDetailModal comment={comment} onClose={() => setShowModal(false)} />
      )}
    </>
  );
}

/**
 * Modal for displaying detailed comment processing results
 */
function CommentDetailModal({ 
  comment, 
  onClose 
}: { 
  comment: YouTubeCommentWithStats; 
  onClose: () => void;
}) {
  const { processing } = comment;
  const hasAnyProcessing = processing.sentiment || processing.intention || 
    processing.travel_type || processing.locations.length > 0 || 
    (processing.asca_aspects && processing.asca_aspects.length > 0);

  return (
    <div 
      style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }} 
      className="z-50 flex items-center justify-center w-full h-full relative"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Backdrop */}
      {/* <div 
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
        className="-z-40 bg-black/50 backdrop-blur-sm bg-opacity-50 bg-gray-50"
        onClick={onClose}
      /> */}
      
      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl overflow-hidden flex w-[50%] h-[70%]">
        {/* Header */}  
        <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-blue-600" />
            <h2 className="font-semibold text-gray-900">Chi tiết xử lý Comment</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-4 overflow-y-scroll min-h-max max-h-max">
          {/* Comment Info */}
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
              <span>👤 {comment.author_name || 'Anonymous'}</span>
              <span>📅 {new Date(comment.published_at).toLocaleDateString('vi-VN')}</span>
            </div>
            <p className="text-sm text-gray-800">{comment.text}</p>
            {comment.like_count > 0 && (
              <div className="mt-2 text-xs text-gray-500">
                👍 {comment.like_count} likes
              </div>
            )}
          </div>

          {!hasAnyProcessing ? (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p>Chưa có dữ liệu xử lý cho comment này</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* ASCA Analysis */}
              <div className={`p-3 rounded-lg border md:col-span-2 ${
                processing.asca_aspects && processing.asca_aspects.length > 0
                  ? 'bg-green-50 border-green-200'
                  : 'bg-amber-50 border-amber-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-gray-600" />
                    <span className="font-medium text-sm text-gray-900">ASCA Analysis</span>
                  </div>
                  {processing.asca_aspects && processing.asca_aspects.length > 0 ? (
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                  )}
                </div>
                
                {processing.asca_aspects && processing.asca_aspects.length > 0 ? (
                  <div className="space-y-2">
                    {/* Summary */}
                    <div className="flex gap-4 text-xs pb-2 border-b border-gray-200">
                      <div className="flex items-center gap-1">
                        <span className="inline-block w-2 h-2 rounded-full bg-green-500"></span>
                        <span className="text-gray-600">
                          Positive: {processing.asca_aspects.filter(a => a.sentiment === 'positive').length}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="inline-block w-2 h-2 rounded-full bg-red-500"></span>
                        <span className="text-gray-600">
                          Negative: {processing.asca_aspects.filter(a => a.sentiment === 'negative').length}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="inline-block w-2 h-2 rounded-full bg-gray-400"></span>
                        <span className="text-gray-600">
                          Neutral: {processing.asca_aspects.filter(a => a.sentiment === 'neutral').length}
                        </span>
                      </div>
                    </div>
                    
                    {/* Aspect List */}
                    <div className="space-y-2">
                      {processing.asca_aspects.map((aspect, i) => (
                        <div 
                          key={i}
                          className={`p-2 rounded-lg border ${
                            aspect.sentiment === 'positive' ? 'bg-green-50 border-green-200' :
                            aspect.sentiment === 'negative' ? 'bg-red-50 border-red-200' :
                            'bg-gray-50 border-gray-200'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className={`text-sm font-medium ${
                              aspect.sentiment === 'positive' ? 'text-green-800' :
                              aspect.sentiment === 'negative' ? 'text-red-800' :
                              'text-gray-800'
                            }`}>
                              {aspect.sentiment === 'positive' ? '👍' : aspect.sentiment === 'negative' ? '👎' : '😐'}
                              {' '}{aspect.category}
                            </span>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              aspect.sentiment === 'positive' ? 'bg-green-200 text-green-800' :
                              aspect.sentiment === 'negative' ? 'bg-red-200 text-red-800' :
                              'bg-gray-200 text-gray-800'
                            }`}>
                              {aspect.sentiment}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-amber-700 italic">
                    ⚠️ Chưa xử lý ASCA
                  </div>
                )}
              </div>

              {/* Intention */}
              <div className={`p-3 rounded-lg border ${
                processing.intention
                  ? 'bg-green-50 border-green-200'
                  : 'bg-amber-50 border-amber-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-gray-600" />
                    <span className="font-medium text-sm text-gray-900">Intention</span>
                  </div>
                  {processing.intention ? (
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                  )}
                </div>
                {processing.intention ? (
                  <div className="text-sm font-medium text-purple-700">
                    🎯 {processing.intention}
                  </div>
                ) : (
                  <div className="text-sm text-amber-700 italic">
                    ⚠️ Chưa xác định
                  </div>
                )}
              </div>

              {/* Traveling Type */}
              <div className={`p-3 rounded-lg border ${
                processing.travel_type
                  ? 'bg-green-50 border-green-200'
                  : 'bg-amber-50 border-amber-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Plane className="w-4 h-4 text-gray-600" />
                    <span className="font-medium text-sm text-gray-900">Traveling Type</span>
                  </div>
                  {processing.travel_type ? (
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                  )}
                </div>
                {processing.travel_type ? (
                  <div className="text-sm font-medium text-amber-700">
                    ✈️ {processing.travel_type}
                  </div>
                ) : (
                  <div className="text-sm text-amber-700 italic">
                    ⚠️ Chưa xác định
                  </div>
                )}
              </div>

              {/* Locations */}
              <div className={`p-3 rounded-lg border md:col-span-2 ${
                processing.locations.length > 0
                  ? 'bg-green-50 border-green-200'
                  : 'bg-amber-50 border-amber-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-gray-600" />
                    <span className="font-medium text-sm text-gray-900">Locations</span>
                  </div>
                  {processing.locations.length > 0 ? (
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                  )}
                </div>
                {processing.locations.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {processing.locations.map((loc, i) => (
                      <span key={i} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                        📍 {loc}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-amber-700 italic">
                    ⚠️ Không phát hiện địa điểm
                  </div>
                )}
              </div>
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
