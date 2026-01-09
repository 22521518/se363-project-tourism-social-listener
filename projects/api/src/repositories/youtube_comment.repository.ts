import { query } from "../database/connection";
import { IntentionType } from "../entities/intention.entity";
import { TravelingType } from "../entities/traveling_type.entity";
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

  intention_type: IntentionType;
  traveling_type: TravelingType;
}

export interface YoutubeCommentListWithMeta {
  data: YouTubeComment[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}
export class YouTubeCommentRepository {
  /**
   * Get all YouTube comments.
   */
  async findAll(
    limit: number,
    offset: number,
    timeRange = "all"
  ): Promise<YoutubeCommentListWithMeta> {
    // Changed: Return single object, not array
    const params: any[] = [];
    let paramIndex = 1;

    // Build WHERE conditions
    const conditions: string[] = [];

    // Time range filter
    if (timeRange !== "all") {
      const timeCondition = this.getTimeRangeCondition(timeRange);
      if (timeCondition) {
        conditions.push(timeCondition);
      }
    }

    const whereClause =
      conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

    // Get total count
    const countSql = `
      SELECT COUNT(DISTINCT yc.id) as total
      FROM youtube_comments yc
      ${whereClause}
    `;
    const countResult = await query<{ total: string }>(
      countSql,
      params.slice()
    );
    const total = parseInt(countResult[0]?.total || "0");

    // Add limit and offset
    params.push(limit, offset);

    // Get paginated data
    const sql = `
      SELECT yc.*
      FROM youtube_comments yc
      ${whereClause}
      ORDER BY yc.created_at DESC, yc.id DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    const rows = await query<RawYoutubeCommentRow>(sql, params);
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

  async findByVideoId(
    videoId: string,
    limit: number,
    offset: number,
    timeRange = "all"
  ): Promise<YoutubeCommentListWithMeta> {
    const params: any[] = [];
    let paramIndex = 1;

    // Add videoId as first parameter
    params.push(videoId);
    const videoIdParam = paramIndex;
    paramIndex++;

    // Build WHERE conditions
    const conditions: string[] = [`yc.video_id = $${videoIdParam}`];


    // Time range filter
    if (timeRange !== "all") {
      const timeCondition = this.getTimeRangeCondition(timeRange);
      if (timeCondition) {
        conditions.push(timeCondition);
      }
    }

    const whereClause =
      conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

    // Get total count
    const countSql = `
      SELECT COUNT(DISTINCT yc.id) as total
      FROM youtube_comments yc
      ${whereClause}
    `;
    const countResult = await query<{ total: string }>(
      countSql,
      params.slice()
    );
    const total = parseInt(countResult[0]?.total || "0");

    // Add limit and offset
    params.push(limit, offset);

    // Get paginated data
    const sql = `
      SELECT yc.*
      FROM youtube_comments yc
      ${whereClause}
      ORDER BY yc.created_at DESC, yc.id DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    const rows = await query<RawYoutubeCommentRow>(sql, params);
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

  async findIntentionByVideoId(
    videoId: string,
    limit: number,
    offset: number,
    intention_type = "all",
    timeRange = "all"
  ): Promise<YoutubeCommentListWithMeta> {
    const params: any[] = [];
    let paramIndex = 1;

    // Add videoId as first parameter
    params.push(videoId);
    const videoIdParam = paramIndex;
    paramIndex++;

    // Build WHERE conditions
    const conditions: string[] = [`yc.video_id = $${videoIdParam}`];

    // Intention type filter
    if (intention_type !== "all") {
      conditions.push(`i.intention_type = $${paramIndex}`);
      params.push(intention_type.toUpperCase());
      paramIndex++;
    }


    // Time range filter
    if (timeRange !== "all") {
      const timeCondition = this.getTimeRangeCondition(timeRange);
      if (timeCondition) {
        conditions.push(timeCondition);
      }
    }

    const whereClause =
      conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

    // Get total count
    const countSql = `
      SELECT COUNT(DISTINCT yc.id) as total
      FROM youtube_comments yc
      JOIN intentions i ON yc.id = i.source_id
      ${whereClause}
    `;
    const countResult = await query<{ total: string }>(
      countSql,
      params.slice()
    );
    const total = parseInt(countResult[0]?.total || "0");

    // Add limit and offset
    params.push(limit, offset);

    // Get paginated data
    const sql = `
      SELECT yc.*, i.intention_type AS intention_type
      FROM youtube_comments yc
      JOIN intentions i ON yc.id = i.source_id
      ${whereClause}
      ORDER BY yc.created_at DESC, yc.id DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    const rows = await query<RawYoutubeCommentRow>(sql, params);
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
  async findTravelingTypeByVideoId(
    videoId: string,
    limit: number,
    offset: number,
    traveling_type = "all",
    timeRange = "all"
  ): Promise<YoutubeCommentListWithMeta> {
    const params: any[] = [];
    let paramIndex = 1;

    // Add videoId as first parameter
    params.push(videoId);
    const videoIdParam = paramIndex;
    paramIndex++;

    // Build WHERE conditions
    const conditions: string[] = [`yc.video_id = $${videoIdParam}`];


    // Traveling type filter
    if (traveling_type !== "all") {
      conditions.push(`t.traveling_type = $${paramIndex}`);
      params.push(traveling_type.toUpperCase());
      paramIndex++;
    }

    // Time range filter
    if (timeRange !== "all") {
      const timeCondition = this.getTimeRangeCondition(timeRange);
      if (timeCondition) {
        conditions.push(timeCondition);
      }
    }

    const whereClause =
      conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

    // Get total count
    const countSql = `
      SELECT COUNT(DISTINCT yc.id) as total
      FROM youtube_comments yc
      JOIN traveling_types t ON yc.id = t.source_id
      ${whereClause}
    `;
    const countResult = await query<{ total: string }>(
      countSql,
      params.slice()
    );
    const total = parseInt(countResult[0]?.total || "0");

    // Add limit and offset
    params.push(limit, offset);

    // Get paginated data
    const sql = `
      SELECT yc.*, t.traveling_type AS traveling_type
      FROM youtube_comments yc
      JOIN traveling_types t ON yc.id = t.source_id
      ${whereClause}
      ORDER BY yc.created_at DESC, yc.id DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    const rows = await query<RawYoutubeCommentRow>(sql, params);
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

      intention_type: row.intention_type,
      traveling_type: row.traveling_type,
    };
  }
  private getTimeRangeCondition(timeRange: string): string | null {
    const timeRangeMap: { [key: string]: string } = {
      "24h": "yc.created_at >= NOW() - INTERVAL '24 hours'",
      "7d": "yc.created_at >= NOW() - INTERVAL '7 days'",
      "30d": "yc.created_at >= NOW() - INTERVAL '30 days'",
      "90d": "yc.created_at >= NOW() - INTERVAL '90 days'",
      "6m": "yc.created_at >= NOW() - INTERVAL '6 months'",
      "1y": "yc.created_at >= NOW() - INTERVAL '1 year'",
    };

    return timeRangeMap[timeRange] || null;
  }
}

export const youtubeCommentRepository = new YouTubeCommentRepository();
