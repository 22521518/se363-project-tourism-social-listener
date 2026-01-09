export interface YoutubeVideo {
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
  tags: string[];
  category_id: string | null;
  created_at: Date;
  updated_at: Date;

  processed_intentions_count: number;
  processed_traveling_types_count: number;

  channel: {
    title: string;
    thumbnail_url: string | null;
    country: string | null;
  };
}

export interface YoutubeVideoListWithMeta {
  data: YoutubeVideo[];
  meta: YoutubeVideoListMeta;
}

export interface YoutubeVideoListMeta {
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}
