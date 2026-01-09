import React, { useState } from "react";
import {
  ThumbsUp,
  MessageSquare,
  Calendar,
  User,
  ChevronDown,
  ChevronUp,
  Tag,
  Plane,
  Target,
} from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import LabelBadge from "./LabelBadge";
import { TRAVEL_COLORS } from "../types/traveling-type";
import { INTENTION_COLORS } from "../types/intention";

interface YoutubeComment {
  id: string;
  video_id: string;
  author_display_name: string;
  author_channel_id: string | null;
  text: string | null;
  like_count: number | null;
  published_at: Date;
  updated_at_youtube: Date;
  parent_id: string | null;
  reply_count: number | null;
  created_at: Date;
  updated_at: Date;
  intention_type: string;
  traveling_type: string;
}

export default function CommentCard({ comment }: { comment: YoutubeComment }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatNumber = (num: number | null) => {
    if (!num) return "0";
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const formatDate = (date: Date | string) => {
    const d = typeof date === "string" ? new Date(date) : date;
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatRelativeTime = (date: Date | string) => {
    const d = typeof date === "string" ? new Date(date) : date;
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    const diffMonths = Math.floor(diffMs / 2592000000);
    const diffYears = Math.floor(diffMs / 31536000000);

    if (diffMins < 60)
      return `${diffMins} minute${diffMins !== 1 ? "s" : ""} ago`;
    if (diffHours < 24)
      return `${diffHours} hour${diffHours !== 1 ? "s" : ""} ago`;
    if (diffDays < 30) return `${diffDays} day${diffDays !== 1 ? "s" : ""} ago`;
    if (diffMonths < 12)
      return `${diffMonths} month${diffMonths !== 1 ? "s" : ""} ago`;
    return `${diffYears} year${diffYears !== 1 ? "s" : ""} ago`;
  };

  const getTravelingTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      business: "bg-blue-100 text-blue-700",
      leisure: "bg-green-100 text-green-700",
      adventure: "bg-orange-100 text-orange-700",
      backpacking: "bg-yellow-100 text-yellow-700",
      luxury: "bg-purple-100 text-purple-700",
      budget: "bg-teal-100 text-teal-700",
      solo: "bg-pink-100 text-pink-700",
      group: "bg-indigo-100 text-indigo-700",
      family: "bg-red-100 text-red-700",
      romantic: "bg-rose-100 text-rose-700",
    };
    return colors[type.toLowerCase()] || "bg-gray-100 text-gray-700";
  };

  const getIntentionTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      question: "bg-blue-100 text-blue-700",
      feedback: "bg-green-100 text-green-700",
      complaint: "bg-red-100 text-red-700",
      suggestion: "bg-yellow-100 text-yellow-700",
      praise: "bg-purple-100 text-purple-700",
      request: "bg-orange-100 text-orange-700",
      discussion: "bg-teal-100 text-teal-700",
      spam: "bg-gray-100 text-gray-700",
    };
    return colors[type.toLowerCase()] || "bg-gray-100 text-gray-700";
  };

  const truncateText = (text: string | null, maxLength: number) => {
    if (!text) return "";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  const isReply = comment.parent_id !== null;

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow`}
      style={{
        flex: "1 1 300px",
        height: "fit-content",
      }}
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start gap-3 mb-3">
          {/* Author Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <a
                href={
                  comment.author_channel_id
                    ? `https://www.youtube.com/channel/${comment.author_channel_id}`
                    : "#"
                }
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold text-gray-900 hover:text-blue-600 transition-colors"
              >
                {comment.author_display_name}
              </a>
              {isReply && (
                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                  Reply
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              {formatRelativeTime(comment.published_at)}
            </p>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-3 text-sm text-gray-500">
            {comment.like_count !== null && comment.like_count > 0 && (
              <div className="flex items-center gap-1">
                <ThumbsUp className="w-4 h-4" />
                <span>{formatNumber(comment.like_count)}</span>
              </div>
            )}
            {comment.reply_count !== null && comment.reply_count > 0 && (
              <div className="flex items-center gap-1">
                <MessageSquare className="w-4 h-4" />
                <span>{comment.reply_count}</span>
              </div>
            )}
          </div>
        </div>

        {/* Comment Text */}
        <div className="mb-3">
          <p className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">
            {isExpanded ? comment.text : truncateText(comment.text, 200)}
          </p>
          {comment.text && comment.text.length > 200 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-blue-600 hover:text-blue-700 text-sm mt-1 font-medium"
            >
              {isExpanded ? "Show less" : "Read more"}
            </button>
          )}
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-3">
          {comment?.traveling_type && (
            <LabelBadge
              type={"traveling_type"}
              color={TRAVEL_COLORS[comment.traveling_type]}
              label={comment.traveling_type}
            />
          )}
          {comment?.intention_type && (
            <LabelBadge
              type={"intention"}
              color={INTENTION_COLORS[comment.intention_type]}
              label={comment.intention_type}
            />
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {formatDate(comment.created_at)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
