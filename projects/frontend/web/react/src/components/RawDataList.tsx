import { useState } from "react";
import {
  Loader2,
  MessageCircle,
  Globe,
  ExternalLink,
  ThumbsUp,
  Calendar,
} from "lucide-react";
import {
  RawDataItem,
  ProcessingFilter,
  ProcessingTask,
  YouTubeCommentMetadata,
  WebCrawlMetadata,
} from "../types/raw_data";
import { useRawYouTubeData, useRawWebCrawlData } from "../hooks/useRawData";
import {
  ProcessingStatusBadge,
  ProcessingStatusFilter,
} from "./ProcessingStatusBadge";
import { TaskDetailModal } from "./TaskDetailModal";

interface RawDataListProps {
  sourceType: "youtube" | "webcrawl";
  taskFilter?: ProcessingTask | "all";
}

/**
 * List component for displaying raw data with processing status
 */
export function RawDataList({
  sourceType,
  taskFilter = "all",
}: RawDataListProps) {
  const [processingFilter, setProcessingFilter] =
    useState<ProcessingFilter>("all");
  const [task, setTask] = useState<ProcessingTask | "all">(taskFilter);
  const [selectedItem, setSelectedItem] = useState<RawDataItem | null>(null);

  const youtubeResult = useRawYouTubeData(processingFilter, task);
  const webcrawlResult = useRawWebCrawlData(processingFilter, task);

  const { data, meta, summary, loading, error, fetchMore } =
    sourceType === "youtube" ? youtubeResult : webcrawlResult;

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-6">
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {summary.total_items}
              </div>
              <div className="text-sm text-gray-600">Total Items</div>
            </div>
            <div className="h-10 w-px bg-gray-200" />
            <div className="flex gap-4 text-sm">
              {(
                [
                  "asca",
                  "intention",
                  "location_extraction",
                  "traveling_type",
                ] as const
              ).map((t) => (
                <div key={t} className="text-center">
                  <div className="font-semibold text-gray-900">
                    {summary.processed_counts[t]}
                  </div>
                  <div className="text-gray-500 text-xs capitalize">
                    {t.replace("_", " ")}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <ProcessingStatusFilter
            value={processingFilter}
            onChange={setProcessingFilter}
            task={task}
            onTaskChange={setTask}
          />
        </div>
      </div>

      {/* Data List */}
      <div className="space-y-3">
        {loading && data.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            <span className="ml-2 text-gray-600">Loading data...</span>
          </div>
        ) : error && data.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center text-gray-500">
            {error}
          </div>
        ) : data.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center text-gray-500">
            No data found matching your filters
          </div>
        ) : (
          <>
            {data.map((item) => (
              <RawDataItemCard
                key={item.id}
                item={item}
                onClick={() => setSelectedItem(item)}
              />
            ))}

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
                  `Load More (${meta.total - data.length} remaining)`
                )}
              </button>
            )}
          </>
        )}
      </div>

      {/* Task Detail Modal */}
      <TaskDetailModal
        item={selectedItem}
        onClose={() => setSelectedItem(null)}
      />
    </div>
  );
}

/**
 * Card component for a single raw data item
 */
function RawDataItemCard({
  item,
  onClick,
}: {
  item: RawDataItem;
  onClick?: () => void;
}) {
  const isYouTube = item.source_type === "youtube_comment";
  const metadata = item.metadata;

  return (
    <div
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 cursor-pointer hover:border-blue-300 hover:shadow-md transition-all"
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2">
          {isYouTube ? (
            <MessageCircle className="w-4 h-4 text-red-500" />
          ) : (
            <Globe className="w-4 h-4 text-blue-500" />
          )}
          <span className="text-xs text-gray-500">
            {isYouTube ? "YouTube Comment" : "Web Crawl"}
          </span>
        </div>
        <ProcessingStatusBadge status={item.processing_status} compact />
      </div>

      {/* Content */}
      <p className="text-sm text-gray-800 mb-3 line-clamp-3">
        {item.text || "(No text content)"}
      </p>

      {/* Metadata */}
      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
        {isYouTube ? (
          <>
            <span className="font-medium text-gray-700">
              {(metadata as YouTubeCommentMetadata).author_name || "Anonymous"}
            </span>
            {(metadata as YouTubeCommentMetadata).video_title && (
              <span className="truncate max-w-xs">
                📹 {(metadata as YouTubeCommentMetadata).video_title}
              </span>
            )}
            <span className="flex items-center gap-1">
              <ThumbsUp className="w-3 h-3" />
              {(metadata as YouTubeCommentMetadata).like_count}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(
                (metadata as YouTubeCommentMetadata).published_at
              ).toLocaleDateString("vi-VN")}
            </span>
          </>
        ) : (
          <>
            <a
              href={(metadata as WebCrawlMetadata).url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline flex items-center gap-1 truncate max-w-sm"
            >
              {(metadata as WebCrawlMetadata).url}
              <ExternalLink className="w-3 h-3 flex-shrink-0" />
            </a>
            <span className="px-2 py-1 bg-gray-100 rounded">
              {(metadata as WebCrawlMetadata).content_type}
            </span>
          </>
        )}
      </div>

      {/* Processing Status Details */}
      <div
        style={{
          marginTop: 6,
          paddingTop: 6,
        }}
        className=" border-t border-gray-100"
      >
        <ProcessingStatusBadge status={item.processing_status} />
      </div>
    </div>
  );
}
