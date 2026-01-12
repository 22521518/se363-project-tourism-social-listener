/**
 * Types for YouTube videos and comments with processing stats
 * Used in the PostAnalysis page for social listening
 */

export interface SentimentBreakdown {
  positive: number;
  negative: number;
  neutral: number;
}

export interface TopItem {
  name: string;
  count: number;
}

export interface ASCACategoryBreakdown {
  category: string;
  positive: number;
  negative: number;
  neutral: number;
}

export interface VideoProcessingStats {
  total_comments: number;
  processed_count: number;
  sentiment: SentimentBreakdown;
  top_intentions: TopItem[];
  top_travel_types: TopItem[];
  top_locations: TopItem[];
  asca_categories: ASCACategoryBreakdown[];
}

export interface YouTubeVideoWithStats {
  id: string;
  channel_id: string;
  title: string;
  description: string | null;
  published_at: string;
  thumbnail_url: string | null;
  view_count: number | null;
  like_count: number | null;
  comment_count: number | null;
  duration: string | null;
  channel: {
    title: string;
    thumbnail_url: string | null;
    country: string | null;
  };
  stats: VideoProcessingStats;
}

export interface CommentProcessing {
  sentiment: 'positive' | 'negative' | 'neutral' | null;
  intention: string | null;
  travel_type: string | null;
  locations: string[];
  asca_aspects: Array<{
    category: string;
    sentiment: string;
  }>;
}

export interface YouTubeCommentWithStats {
  id: string;
  video_id: string;
  text: string;
  author_name: string | null;
  like_count: number;
  published_at: string;
  processing: CommentProcessing;
}

export interface VideosWithStatsResponse {
  success: boolean;
  data: YouTubeVideoWithStats[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}

export interface CommentsWithStatsResponse {
  success: boolean;
  data: YouTubeCommentWithStats[];
  meta: {
    total: number;
    hasMore: boolean;
  };
}

// Color maps for badges
export const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#22c55e',
  negative: '#ef4444',
  neutral: '#6b7280',
};

export const SENTIMENT_BG: Record<string, string> = {
  positive: '#dcfce7',
  negative: '#fee2e2',
  neutral: '#f3f4f6',
};

export const INTENTION_COLORS: Record<string, string> = {
  QUESTION: "#3b82f6",
  FEEDBACK: "#10b981",
  COMPLAINT: "#f59e0b",
  SUGGESTION: "#8b5cf6",
  PRAISE: "#ec4899",
  REQUEST: "#06b6d4",
  DISCUSSION: "#f97316",
  SPAM: "#ef4444",
  OTHER: "#6b7280",
};

export const TRAVEL_TYPE_COLORS: Record<string, string> = {
  BUSINESS: "#3b82f6",
  LEISURE: "#10b981",
  ADVENTURE: "#f59e0b",
  BACKPACKING: "#8b5cf6",
  LUXURY: "#ec4899",
  BUDGET: "#06b6d4",
  SOLO: "#06b6d4",
  GROUP: "#f97316",
  FAMILY: "#ef4444",
  ROMANTIC: "#9c032e",
  OTHER: "#6b7280",
};
