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

  processed_intentions_count: number;
  processed_traveling_types_count: number;

  channel_title: string;
  channel_thumbnail_url: string | null;
  channel_country: string | null;
}

export interface YoutubeVideoListWithMeta {
  data: YouTubeVideo[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}
export class YouTubeVideoRepository {
  /**
   * Get all YouTube videos.
   */
  commentRepository: any;

  async findAll(
    limit = 20,
    offset = 0,
    channel = "all",
    timeRange = "all"
  ): Promise<YoutubeVideoListWithMeta> {
    const params: any[] = [];
    let paramIndex = 1;

    // Build WHERE conditions
    const conditions: string[] = [
      `EXISTS (
        SELECT 1
        FROM youtube_comments c
        WHERE c.video_id = v.id
        AND (
          c.id IN (SELECT source_id FROM traveling_types)
          OR c.id IN (SELECT source_id FROM intentions)
        )
    )`,
    ];

    // Channel filter
    if (channel !== "all") {
      conditions.push(`v.channel_id = $${paramIndex}`);
      params.push(channel);
      paramIndex++;
    }

    // Time range filter
    if (timeRange !== "all") {
      const timeCondition = this.getTimeRangeCondition(timeRange, paramIndex);
      if (timeCondition) {
        conditions.push(timeCondition);
      }
    }

    // Get total count
    const countSql = `
    SELECT COUNT(DISTINCT v.id) as total
    FROM youtube_videos v
    JOIN youtube_channels c ON v.channel_id = c.id
    WHERE ${conditions.join(" AND ")}
  `;
    const countResult = await query<{ total: string }>(
      countSql,
      params.slice(0, params.length)
    );
    const total = parseInt(countResult[0]?.total || "0");

    // Add limit and offset
    params.push(limit, offset);

    const sql = `
      WITH intentions_count AS (
        SELECT source_id AS comment_id, COUNT(*) AS cnt
        FROM intentions
        GROUP BY source_id
      ),
      traveling_count AS (
        SELECT source_id AS comment_id, COUNT(*) AS cnt
        FROM traveling_types
        GROUP BY source_id
      ),
      comment_stats AS (
        SELECT
          yc.video_id,
          COALESCE(SUM(ic.cnt), 0) AS processed_intentions_count,
          COALESCE(SUM(tc.cnt), 0) AS processed_traveling_types_count
        FROM youtube_comments yc
        LEFT JOIN intentions_count ic ON ic.comment_id = yc.id
        LEFT JOIN traveling_count tc ON tc.comment_id = yc.id
        GROUP BY yc.video_id
      )

      SELECT
        v.*,
        c.title AS channel_title,
        c.thumbnail_url AS channel_thumbnail_url,
        c.country AS channel_country,
        COALESCE(cs.processed_intentions_count, 0) AS processed_intentions_count,
        COALESCE(cs.processed_traveling_types_count, 0) AS processed_traveling_types_count
      FROM youtube_videos v
      JOIN youtube_channels c ON v.channel_id = c.id
      LEFT JOIN comment_stats cs ON cs.video_id = v.id
      WHERE ${conditions.join(" AND ")}
      ORDER BY 
        (processed_intentions_count + processed_traveling_types_count) DESC,
        v.created_at DESC,
        v.id DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    const rows = await query<RawYoutubeVideoRow>(sql, params);
    const data = rows.map((row) => this.mapToEntity(row));

    return {
      data,
      meta: {
        total,
        limit,
        offset,
        hasMore: offset + data.length < total,
      },
    };
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

      processed_intentions_count: row.processed_intentions_count,
      processed_traveling_types_count: row.processed_traveling_types_count,
      channel: {
        title: row.channel_title,
        thumbnail_url: row.channel_thumbnail_url,
        country: row.channel_country,
      },
    };
  }

  private getTimeRangeCondition(
    timeRange: string,
    paramIndex: number
  ): string | null {
    const timeRangeMap: { [key: string]: string } = {
      "24h": "v.created_at >= NOW() - INTERVAL '24 hours'",
      "7d": "v.created_at >= NOW() - INTERVAL '7 days'",
      "30d": "v.created_at >= NOW() - INTERVAL '30 days'",
      "90d": "v.created_at >= NOW() - INTERVAL '90 days'",
      "6m": "v.created_at >= NOW() - INTERVAL '6 months'",
      "1y": "v.created_at >= NOW() - INTERVAL '1 year'",
    };

    return timeRangeMap[timeRange] || null;
  }
}

export const youtubeVideoRepository = new YouTubeVideoRepository();
