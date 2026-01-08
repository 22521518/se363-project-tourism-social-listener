import { query } from "../database/connection";
import { YouTubeVideo } from "../entities/youtube_video.entity";

interface RawYoutubeVideoRow {
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

  channel_title: string;
  channel_thumbnail_url: string | null;
}

export class YouTubeVideoRepository {
  /**
   * Get all YouTube videos.
   */
  commentRepository: any;

  async findAll(limit = 20, offset = 0): Promise<YouTubeVideo[]> {
    const sql = `
        SELECT v.*, c.title AS channel_title, c.thumbnail_url AS channel_thumbnail_url
        FROM youtube_videos v
        JOIN youtube_channels c ON v.channel_id = c.id
        WHERE EXISTS (
        SELECT 1
        FROM youtube_comments c
        WHERE c.video_id = v.id
        AND c.id IN (SELECT source_id FROM traveling_types)
        AND c.id IN (SELECT source_id FROM intentions)
        )
        ORDER BY v.created_at DESC, v.id DESC
        LIMIT $1 OFFSET $2
    `;
    const rows = await query<RawYoutubeVideoRow>(sql, [limit, offset]);
    return rows.map((row) => this.mapToEntity(row));
  }

  async findById(id: string): Promise<YouTubeVideo | null> {
    const sql = `
        SELECT v.*, c.title AS channel_title, c.thumbnail_url AS channel_thumbnail_url
        FROM youtube_videos v
        JOIN youtube_channels c ON v.channel_id = c.id
        WHERE v.id = $1
    `;
    const rows = await query<RawYoutubeVideoRow>(sql, [id]);
    return rows.length > 0 ? this.mapToEntity(rows[0]) : null;
  }

  /**
   * Map database row to entity.
   */
  private mapToEntity(row: RawYoutubeVideoRow): YouTubeVideo {
    return {
      id: row.id,
      channel_id: row.channel_id,
      title: row.title,
      description: row.description,
      published_at: row.published_at,
      thumbnail_url: row.thumbnail_url,
      view_count: row.view_count,
      like_count: row.like_count,
      comment_count: row.comment_count,
      duration: row.duration,
      tags: row.tags,
      category_id: row.category_id,
      created_at: row.created_at,
      updated_at: row.updated_at,

      channel: {
        title: row.channel_title,
        thumbnail_url: row.channel_thumbnail_url,
      },
    };
  }
}

export const youtubeVideoRepository = new YouTubeVideoRepository();
