import React from "react";
import { useYoutubeVideoData } from "../hooks/useYoutubeVideoData";
import { useYoutubeVideoDetailData } from "../hooks/useYoutubeVideoDetailData";
import { useParams, useSearchParams } from "react-router";
import {
  ArrowLeft,
  Calendar,
  Clock,
  Database,
  Eye,
  Globe,
  MessageSquare,
  Tag,
  ThumbsUp,
} from "lucide-react";
import { ImageWithFallback } from "../components/figma/ImageWithFallback";
import { AdvancedFilters } from "../components/AdvancedFilters";
import CommentSection from "../components/CommentSection";

export default function PostDetail() {
  const { id } = useParams();
  const { data, loading } = useYoutubeVideoDetailData(id);

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

  const getFlagEmoji = (countryCode: string | null) => {
    if (!countryCode || countryCode.length !== 2) return "🌐";

    const codePoints = countryCode
      .toUpperCase()
      .split("")
      .map((char) => 127397 + char.charCodeAt(0));

    return String.fromCodePoint(...codePoints);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-600">Video not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div
        className=" mx-auto px-4 sm:px-6 lg:px-8 py-6"
        style={{ maxWidth: 1920 }}
      >
        {/* Back Button */}
        <button
          onClick={() => window.history.back()}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to videos</span>
        </button>

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 6,
          }}
        >
          {/* Sidebar - Right Column */}
          <div
            style={{
              flex: "1 1 300px",
              display: "flex",
              flexDirection: "column",
              gap: 6,
            }}
          >
            {/* Video Player Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="relative w-full" style={{ aspectRatio: "16/9" }}>
                <iframe
                  src={`https://www.youtube.com/embed/${data.id}`}
                  title={data.title}
                  className="absolute inset-0 w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>

              <div className="p-6">
                {/* Title */}
                <h1 className="text-2xl font-bold text-gray-900 mb-4">
                  {data.title}
                </h1>

                {/* Channel Info */}
                <a
                  href={`https://www.youtube.com/channel/${data.channel_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors mb-4"
                >
                  <ImageWithFallback
                    src={data.channel.thumbnail_url || ""}
                    alt={data.channel.title}
                    className="rounded-full object-cover flex-shrink-0"
                    style={{ width: 48, height: 48 }}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">
                        {data.channel.title}
                      </span>
                      <span className="text-lg">
                        {getFlagEmoji(data.channel.country)}
                      </span>
                    </div>
                  </div>
                </a>

                {/* Metrics */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "auto auto auto",
                    gap: 12,
                  }}
                >
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <Eye className="w-5 h-5 text-gray-600" />
                      <p className="text-sm text-gray-600">Views</p>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatNumber(data.view_count)}
                    </p>
                  </div>

                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <ThumbsUp className="w-5 h-5 text-gray-600" />
                      <p className="text-sm text-gray-600">Likes</p>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatNumber(data.like_count)}
                    </p>
                  </div>

                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <MessageSquare className="w-5 h-5 text-gray-600" />
                      <p className="text-sm text-gray-600">Comments</p>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatNumber(data.comment_count)}
                    </p>
                  </div>
                </div>

                {/* Description */}
                {data.description && (
                  <div className="border-t border-gray-200 pt-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Description
                    </h3>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                      {data.description}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Video Details Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Video Details
              </h3>

              <ul
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 12,
                }}
              >
                <div
                  className="flex items-start gap-3"
                  style={{
                    flex: "1 1 40%",
                  }}
                >
                  <Clock className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Duration</p>
                    <p className="text-sm font-medium text-gray-900">
                      {formatDuration(data.duration)}
                    </p>
                  </div>
                </div>

                <div
                  className="flex items-start gap-3"
                  style={{
                    flex: "1 1 40%",
                  }}
                >
                  <Calendar className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Published</p>
                    <p className="text-sm font-medium text-gray-900">
                      {formatDate(data.published_at)}
                    </p>
                  </div>
                </div>

                <div
                  className="flex items-start gap-3"
                  style={{
                    flex: "1 1 40%",
                  }}
                >
                  <Database className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Last Updated</p>
                    <p className="text-sm font-medium text-gray-900">
                      {formatDate(data.updated_at)}
                    </p>
                  </div>
                </div>

                {data.category_id && (
                  <div
                    className="flex items-start gap-3"
                    style={{
                      flex: "1 1 40%",
                    }}
                  >
                    <Globe className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Category ID</p>
                      <p className="text-sm font-medium text-gray-900">
                        {data.category_id}
                      </p>
                    </div>
                  </div>
                )}
              </ul>
            </div>

            {/* Tags Section */}
            {data.tags && data.tags.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Tags ({data.tags.length})
                </h3>
                <div
                  className="flex flex-wrap gap-2"
                  style={{
                    maxHeight: 300,
                    overflow: "auto",
                  }}
                >
                  {data.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full text-sm"
                    >
                      <Tag className="w-3 h-3" />
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {/* Engagement Statistics Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Engagement Statistics
              </h3>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">Total Views</span>
                  <span className="text-sm font-bold text-gray-900">
                    {data.view_count?.toLocaleString() || "0"}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">Total Likes</span>
                  <span className="text-sm font-bold text-gray-900">
                    {data.like_count?.toLocaleString() || "0"}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">Total Comments</span>
                  <span className="text-sm font-bold text-gray-900">
                    {data.comment_count?.toLocaleString() || "0"}
                  </span>
                </div>

                {data.view_count && data.like_count && data.view_count > 0 && (
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm font-medium text-blue-700">
                      Like Rate
                    </span>
                    <span className="text-sm font-bold text-blue-900">
                      {((data.like_count / data.view_count) * 100).toFixed(2)}%
                    </span>
                  </div>
                )}

                {data.view_count &&
                  data.comment_count &&
                  data.view_count > 0 && (
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <span className="text-sm font-medium text-green-700">
                        Comment Rate
                      </span>
                      <span className="text-sm font-bold text-green-900">
                        {((data.comment_count / data.view_count) * 100).toFixed(
                          2
                        )}
                        %
                      </span>
                    </div>
                  )}
              </div>
            </div>

            {/* Technical Details Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Technical Details
              </h3>

              <div className="space-y-3">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Video ID</p>
                  <p className="text-xs text-gray-900 font-mono break-all bg-gray-50 p-2 rounded">
                    {data.id}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-gray-500 mb-1">Channel ID</p>
                  <p className="text-xs text-gray-900 font-mono break-all bg-gray-50 p-2 rounded">
                    {data.channel_id}
                  </p>
                </div>
              </div>
            </div>

            {/* Watch on YouTube Button */}
            <a
              href={`https://www.youtube.com/watch?v=${data.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full px-4 py-3 bg-red-600 text-white text-center rounded-lg hover:bg-red-700 transition-colors font-medium"
            >
              Watch on YouTube
            </a>
          </div>
          {/* Main Content - Left Column */}
          <div
            style={{
              flex: "1 1 700px",
            }}
          >
            {/* Comment List */}

            {id && <CommentSection videoId={id} />}
          </div>
        </div>
      </div>
    </div>
  );
}
