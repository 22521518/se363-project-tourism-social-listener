import { YouTubeChannel } from "./youtube_channel.entity";

export interface YouTubeComment {
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
}