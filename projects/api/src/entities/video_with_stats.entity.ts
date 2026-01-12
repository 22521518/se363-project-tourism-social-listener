/**
 * YouTube Video with Processing Stats Entity
 * Extended video entity with aggregated stats from all processing tasks
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
  published_at: Date;
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
  published_at: Date;
  processing: CommentProcessing;
}
