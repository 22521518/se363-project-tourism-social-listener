export interface YoutubeComment {
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

export interface YoutubeCommentListWithMeta {
  data: YoutubeComment[];
  meta: YoutubeCommentListMeta;
}

export interface YoutubeCommentListMeta {
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}
