import { useState } from 'react';
import {
  Globe,
  Star,
  MessageCircle,
  BookOpen,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Loader2,
} from 'lucide-react';
import { useWebCrawlData } from '../hooks/useWebCrawlData';
import { CrawlResult, ContentType, CONTENT_TYPE_COLORS } from '../types/web_crawl';

interface WebCrawlResultsProps {
  contentType?: ContentType | 'all';
}

/**
 * Component for displaying web crawl results including reviews, comments, and blog sections.
 */
export function WebCrawlResults({ contentType = 'all' }: WebCrawlResultsProps) {
  const { data, meta, loading, error, fetchMore } = useWebCrawlData(contentType);

  // Handle loading state
  if (loading && (!data || data.length === 0)) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading web crawl data...</span>
        </div>
      </div>
    );
  }

  // Handle error state
  if (error && (!data || data.length === 0)) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="w-5 h-5 text-blue-600" />
          <h2 className="text-gray-900">Web Crawl Results</h2>
        </div>
        <div className="text-sm text-gray-500 py-4 text-center">
          No web crawl data available yet
        </div>
      </div>
    );
  }

  // Handle empty data
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="w-5 h-5 text-blue-600" />
          <h2 className="text-gray-900">Web Crawl Results</h2>
        </div>
        <div className="text-sm text-gray-500 py-4 text-center">
          No web crawl data available
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-blue-600" />
            <div>
              <h2 className="text-gray-900">Web Crawl Results</h2>
              <p className="text-sm text-gray-600">
                {meta.total} URLs crawled
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-4">
        {data.map((result) => (
          <CrawlResultCard key={result.id || result.request_id} result={result} />
        ))}
      </div>

      {/* Load More */}
      {meta.hasMore && (
        <button
          disabled={loading}
          onClick={fetchMore}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Loading...
            </>
          ) : (
            'Load More'
          )}
        </button>
      )}
    </div>
  );
}

/**
 * Card component for a single crawl result.
 */
function CrawlResultCard({ result }: { result: CrawlResult }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const { content } = result;

  const reviewCount = content.reviews?.length || 0;
  const commentCount = content.comments?.length || 0;
  const blogSectionCount = content.blog_sections?.length || 0;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-gray-900 truncate">
              {content.title || 'Untitled Page'}
            </h3>
            <a
              href={result.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:underline flex items-center gap-1 truncate"
            >
              {result.url}
              <ExternalLink className="w-3 h-3 flex-shrink-0" />
            </a>
          </div>

          <span
            className="px-2 py-1 text-xs rounded-full flex-shrink-0"
            style={{
              backgroundColor: `${CONTENT_TYPE_COLORS[result.content_type]}20`,
              color: CONTENT_TYPE_COLORS[result.content_type],
            }}
          >
            {result.content_type}
          </span>
        </div>

        {/* Stats */}
        <div className="flex gap-4 mt-3 text-sm text-gray-600">
          {reviewCount > 0 && (
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 text-amber-500" />
              <span>{reviewCount} reviews</span>
            </div>
          )}
          {commentCount > 0 && (
            <div className="flex items-center gap-1">
              <MessageCircle className="w-4 h-4 text-blue-500" />
              <span>{commentCount} comments</span>
            </div>
          )}
          {blogSectionCount > 0 && (
            <div className="flex items-center gap-1">
              <BookOpen className="w-4 h-4 text-purple-500" />
              <span>{blogSectionCount} sections</span>
            </div>
          )}
        </div>
      </div>

      {/* Information Preview */}
      {content.information && (
        <div className="px-4 py-3 bg-gray-50 text-sm text-gray-700">
          <p className={isExpanded ? '' : 'line-clamp-2'}>
            {content.information}
          </p>
        </div>
      )}

      {/* Expand Button */}
      {(reviewCount > 0 || commentCount > 0 || blogSectionCount > 0) && (
        <>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full px-4 py-2 flex items-center justify-center gap-2 text-blue-600 hover:bg-blue-50 transition-colors text-sm"
          >
            {isExpanded ? 'Hide Details' : 'Show Details'}
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          {/* Expanded Content */}
          {isExpanded && (
            <div className="p-4 border-t border-gray-100 space-y-4">
              {/* Reviews */}
              {reviewCount > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <Star className="w-4 h-4 text-amber-500" />
                    Reviews
                  </h4>
                  <div className="space-y-2">
                    {content.reviews.slice(0, 5).map((review, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-amber-50 rounded-lg text-sm"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-gray-900">
                            {review.author || 'Anonymous'}
                          </span>
                          {review.rating && (
                            <span className="text-amber-600">
                              ⭐ {review.rating}
                            </span>
                          )}
                        </div>
                        <p className="text-gray-700">{review.text}</p>
                      </div>
                    ))}
                    {reviewCount > 5 && (
                      <p className="text-sm text-gray-500 text-center">
                        +{reviewCount - 5} more reviews
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Comments */}
              {commentCount > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <MessageCircle className="w-4 h-4 text-blue-500" />
                    Comments
                  </h4>
                  <div className="space-y-2">
                    {content.comments.slice(0, 5).map((comment, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-blue-50 rounded-lg text-sm"
                      >
                        <span className="font-medium text-gray-900">
                          {comment.author || 'Anonymous'}
                        </span>
                        <p className="text-gray-700 mt-1">{comment.text}</p>
                      </div>
                    ))}
                    {commentCount > 5 && (
                      <p className="text-sm text-gray-500 text-center">
                        +{commentCount - 5} more comments
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Blog Sections */}
              {blogSectionCount > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-purple-500" />
                    Blog Sections
                  </h4>
                  <div className="space-y-2">
                    {content.blog_sections.slice(0, 3).map((section, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-purple-50 rounded-lg text-sm"
                      >
                        <h5 className="font-medium text-gray-900">
                          {section.heading}
                        </h5>
                        <p className="text-gray-700 mt-1 line-clamp-3">
                          {section.text}
                        </p>
                      </div>
                    ))}
                    {blogSectionCount > 3 && (
                      <p className="text-sm text-gray-500 text-center">
                        +{blogSectionCount - 3} more sections
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
