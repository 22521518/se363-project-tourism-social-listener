import React, { useState } from "react";
import { YouTubeVideo } from "../types/youtube_video";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import {
  Calendar,
  ChevronDown,
  ChevronUp,
  Clock,
  Eye,
  Globe,
  MessageSquare,
  Tag,
  ThumbsUp,
} from "lucide-react";

// Main Video Card Component
export default function VideoCard({ video }: { video: YouTubeVideo }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatNumber = (num: number | null) => {
    if (!num) return "0";
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toLocaleString();
  };

  const formatDate = (date: Date | string | null) => {
    if (!date) return "Unknown";
    const d = typeof date === "string" ? new Date(date) : date;
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatDuration = (duration: string | null) => {
    if (!duration) return "0:00";

    // Parse ISO 8601 duration format (PT1H2M3S)
    const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
    if (!match) return duration;

    const hours = parseInt(match[1] || "0", 10);
    const minutes = parseInt(match[2] || "0", 10);
    const seconds = parseInt(match[3] || "0", 10);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, "0")}:${seconds
        .toString()
        .padStart(2, "0")}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header with thumbnail */}
      <div className="flex items-start mb-4 gap-4">
        <div
          style={{
            position: "relative",
          }}
        >
          <ImageWithFallback
            src={video.thumbnail_url || ""}
            alt={video.title}
            className="w-40 h-24 rounded-lg object-cover flex-shrink-0"
          />
          {video.duration && (
            <div
              className="absolute bottom-1 right-1 bg-blue-500 text-white text-xs px-2 py-1 rounded"
              style={{
                backgroundColor: "rgba(0, 0, 0, 0.7)",
                position: "absolute",
                bottom: "4px",
                right: "4px",
              }}
            >
              {formatDuration(video.duration)}
            </div>
          )}
        </div>

        <div
          className="flex-1 min-w-0"
          style={{
            gap: 4,
          }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
            {video.title}
          </h3>

          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              <span>{formatDate(video.published_at)}</span>
            </div>

            {video.duration && (
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>{formatDuration(video.duration)}</span>
              </div>
            )}
          </div>

          <button
            className="flex flex-row gap-2"
            style={{
              alignItems: "center",
              padding: 4,
              borderRadius: 8,
              backgroundColor: "#f3f4f6",
              width: "fit-content",
            }}
          >
            <ImageWithFallback
              src={video.channel.thumbnail_url || ""}
              alt={video.channel.title}
              className="rounded-full object-cover flex-shrink-0"
              style={{
                width: 24,
                height: 24,
              }}
            />
            <span
              style={{
                fontWeight: "semibold",
                fontSize: 14,
              }}
            >
              {video.channel.title}
            </span>
          </button>
        </div>
      </div>
      {/* Metrics Grid */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div className="text-center flex-1 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-center gap-2 mb-1">
            <Eye className="w-4 h-4 text-gray-600" />
            <p className="text-xs text-gray-600">Views</p>
          </div>
          <p className="text-lg font-semibold text-gray-900">
            {formatNumber(video.view_count)}
          </p>
        </div>

        <div className="text-center flex-1 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-center gap-2 mb-1">
            <ThumbsUp className="w-4 h-4 text-gray-600" />
            <p className="text-xs text-gray-600">Likes</p>
          </div>
          <p className="text-lg font-semibold text-gray-900">
            {formatNumber(video.like_count)}
          </p>
        </div>

        <div className="text-center flex-1 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-center gap-2 mb-1">
            <MessageSquare className="w-4 h-4 text-gray-600" />
            <p className="text-xs text-gray-600">Comments</p>
          </div>
          <p className="text-lg font-semibold text-gray-900">
            {formatNumber(video.comment_count)}
          </p>
        </div>
      </div>

      {/* Tags */}
      {video.tags.length > 0 && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {video.tags.slice(0, 5).map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs"
              >
                <Tag className="w-3 h-3" />
                {tag}
              </span>
            ))}
            {video.tags.length > 5 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                +{video.tags.length - 5} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Expand/Collapse Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-center gap-2 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
      >
        <span>{isExpanded ? "Hide" : "Show"} detailed information</span>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
          {/* Full Description */}
          {video.description && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">
                Full Description
              </h4>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {video.description}
              </p>
            </div>
          )}

          {/* All Tags */}
          {video.tags.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">
                All Tags ({video.tags.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {video.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs"
                  >
                    <Tag className="w-3 h-3" />
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Additional Details */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">
              Video Details
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-gray-50 p-4 rounded-lg">
              <div>
                <p className="text-xs text-gray-600 mb-1">Video ID</p>
                <p className="text-sm text-gray-900 font-mono break-all">
                  {video.id}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-600 mb-1">Channel ID</p>
                <p className="text-sm text-gray-900 font-mono break-all">
                  {video.channel_id}
                </p>
              </div>

              {video.category_id && (
                <div>
                  <p className="text-xs text-gray-600 mb-1">Category ID</p>
                  <p className="text-sm text-gray-900">{video.category_id}</p>
                </div>
              )}

              <div>
                <p className="text-xs text-gray-600 mb-1">Duration</p>
                <p className="text-sm text-gray-900">
                  {formatDuration(video.duration)}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-600 mb-1">Published</p>
                <p className="text-sm text-gray-900">
                  {formatDate(video.published_at)}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-600 mb-1">Last Updated</p>
                <p className="text-sm text-gray-900">
                  {formatDate(video.updated_at)}
                </p>
              </div>
            </div>
          </div>

          {/* Engagement Statistics */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">
              Engagement Statistics
            </h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-700">Total Views</span>
                <span className="text-sm font-semibold text-gray-900">
                  {video.view_count?.toLocaleString() || "0"}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-700">Total Likes</span>
                <span className="text-sm font-semibold text-gray-900">
                  {video.like_count?.toLocaleString() || "0"}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-700">Total Comments</span>
                <span className="text-sm font-semibold text-gray-900">
                  {video.comment_count?.toLocaleString() || "0"}
                </span>
              </div>
              {video.view_count && video.like_count && (
                <div className="flex items-center justify-between p-3 bg-blue-50 rounded">
                  <span className="text-sm text-blue-700">Like Rate</span>
                  <span className="text-sm font-semibold text-blue-900">
                    {((video.like_count / video.view_count) * 100).toFixed(2)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
