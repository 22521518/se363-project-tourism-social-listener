import { query } from "../database/connection";
import { YouTubeComment } from "../entities/youtube_comment.entity";


interface RawYoutubeCommentRow {
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

export class YouTubeCommentRepository {
  /**
   * Get all YouTube comments.
   */
  async findAll(offset = 0): Promise<YouTubeComment[]> {
    const sql = `
      SELECT *
      FROM youtube_comments yc
      WHERE yc.id IN (SELECT source_id FROM traveling_types)
      AND yc.id IN (SELECT source_id FROM intentions);
      ORDER BY created_at DESC
      OFFSET $2
    `;
    const rows = await query<RawYoutubeCommentRow>(sql, [offset] );
    return rows.map((row) => this.mapToEntity(row));
  }

  async findById(id: string): Promise<YouTubeComment | null> {
    const sql = `
      SELECT *
      FROM youtube_comments
      JOIN intentions ON youtube_comments.id = intentions.source_id
      JOIN traveling_types ON youtube_comments.id = traveling_types.source_id
      WHERE id = $1
    `;
    const rows = await query<RawYoutubeCommentRow>(sql, [id]);
    return rows.length > 0 ? this.mapToEntity(rows[0]) : null;
  }

  async findByVideoId(videoId: string): Promise<YouTubeComment[]> {
    const sql = `
      SELECT *
      FROM youtube_comments
      JOIN intentions ON youtube_comments.id = intentions.source_id
      JOIN traveling_types ON youtube_comments.id = traveling_types.source_id
      WHERE video_id = $1
    `;
    const rows = await query<RawYoutubeCommentRow>(sql, [videoId]);
    return rows.map((row) => this.mapToEntity(row));
  } 

  /**
   * Map database row to entity.
   */
  private mapToEntity(row: RawYoutubeCommentRow): YouTubeComment {
    return {
      id: row.id,
      video_id: row.video_id,
      author_display_name: row.author_display_name,
      author_channel_id: row.author_channel_id,
      text: row.text,
      like_count: row.like_count,
      published_at: row.published_at,
      updated_at_youtube: row.updated_at_youtube,
      parent_id: row.parent_id,
      reply_count: row.reply_count,
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }
}

export const youtubeCommentRepository = new YouTubeCommentRepository();