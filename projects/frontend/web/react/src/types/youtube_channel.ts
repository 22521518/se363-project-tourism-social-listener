export interface YouTubeChannel {
  id: string;
  title: string;
  description: string | null;
  custom_url: string | null;
  published_at: Date;
  thumbnail_url: string | null;
  subscriber_count: number | null;
  video_count: number | null;
  view_count: number | null;
  country: string | null;
  is_tracked: boolean | null;
  last_checked: Date | null;
  created_at: Date;
  updated_at: Date;
}