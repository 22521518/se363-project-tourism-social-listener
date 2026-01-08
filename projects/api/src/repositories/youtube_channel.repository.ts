import { query } from "../database/connection";
import { YouTubeChannel } from "../entities/youtube_channel.entity";

interface RawYoutubeChannelRow {
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

export class YouTubeChannelRepository {
  /**
   * Get all YouTube channels.
   */
  commentRepository: any;

  async findAll(): Promise<YouTubeChannel[]> {
    const sql = `
        SELECT *
        FROM youtube_channels
    `;
    const rows = await query<RawYoutubeChannelRow>(sql);
    return rows.map((row) => this.mapToEntity(row));
  }

  /**
   * Map database row to entity.
   */
  private mapToEntity(row: RawYoutubeChannelRow): YouTubeChannel {
    return {
      id: row.id,
      title: row.title,
      description: row.description,
      custom_url: row.custom_url,
      published_at: row.published_at,
      thumbnail_url: row.thumbnail_url,
      subscriber_count: row.subscriber_count,
      video_count: row.video_count,
      view_count: row.view_count,
      country: row.country,
      is_tracked: row.is_tracked,
      last_checked: row.last_checked,
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }
}

export const youTubeChannelRepository = new YouTubeChannelRepository();
