import { query } from "../database/connection";
import {
  YouTubeVideoWithStats,
  YouTubeCommentWithStats,
  VideoProcessingStats,
  SentimentBreakdown,
  TopItem,
  ASCACategoryBreakdown,
  CommentProcessing,
} from "../entities/video_with_stats.entity";

interface VideoStatsRow {
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
  channel_title: string;
  channel_thumbnail_url: string | null;
  channel_country: string | null;
  // Stats from aggregation
  processed_count: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
}

export interface VideoWithStatsListResponse {
  data: YouTubeVideoWithStats[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}

export class VideoWithStatsRepository {
  /**
   * Get videos with aggregated processing stats
   */
  async findAllWithStats(
    limit = 20,
    offset = 0,
    channel = "all",
    timeRange = "all",
    filters: {
      sentiment?: string;
      intention?: string;
      travelType?: string;
      aspect?: string;
    } = {}
  ): Promise<VideoWithStatsListResponse> {
    const params: unknown[] = [];
    let paramIndex = 1;
    const conditions: string[] = [];

    // Channel filter
    if (channel !== "all") {
      conditions.push(`v.channel_id = $${paramIndex}`);
      params.push(channel);
      paramIndex++;
    }

    // Time range filter
    const timeCondition = this.getTimeRangeCondition(timeRange);
    if (timeCondition) {
      conditions.push(timeCondition);
    }

    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

    // Get total count first
    const countSql = `
      SELECT COUNT(DISTINCT v.id) as total
      FROM youtube_videos v
      ${whereClause}
    `;
    const countResult = await query<{ total: string }>(countSql, params);
    const total = parseInt(countResult[0]?.total || "0", 10);

    // Main query with stats aggregation
    params.push(limit, offset);
    const sql = `
      WITH video_sentiment AS (
        SELECT 
          yc.video_id,
          COUNT(*) as processed_count,
          COUNT(*) FILTER (WHERE ae.aspects IS NOT NULL) as asca_count,
          COUNT(*) FILTER (WHERE i.intention_type IS NOT NULL) as intention_count,
          COUNT(*) FILTER (WHERE tt.traveling_type IS NOT NULL) as travel_type_count,
          COUNT(*) FILTER (WHERE le.locations IS NOT NULL) as location_count
        FROM youtube_comments yc
        LEFT JOIN asca_extractions ae ON ae.source_id = yc.id AND ae.is_deleted = false
        LEFT JOIN intentions i ON i.source_id = yc.id
        LEFT JOIN traveling_types tt ON tt.source_id = yc.id
        LEFT JOIN location_extractions le ON le.source_id = yc.id
        WHERE ae.id IS NOT NULL OR i.id IS NOT NULL OR tt.id IS NOT NULL OR le.id IS NOT NULL
        GROUP BY yc.video_id
      ),
      video_asca_sentiment AS (
        SELECT 
          yc.video_id,
          COUNT(*) FILTER (WHERE aspect->>'sentiment' = 'positive') as positive_count,
          COUNT(*) FILTER (WHERE aspect->>'sentiment' = 'negative') as negative_count,
          COUNT(*) FILTER (WHERE aspect->>'sentiment' = 'neutral') as neutral_count
        FROM youtube_comments yc
        JOIN asca_extractions ae ON ae.source_id = yc.id AND ae.is_deleted = false,
        jsonb_array_elements(ae.aspects) as aspect
        GROUP BY yc.video_id
      )
      SELECT 
        v.id, v.channel_id, v.title, v.description, v.published_at,
        v.thumbnail_url, v.view_count, v.like_count, v.comment_count, v.duration,
        c.title as channel_title, c.thumbnail_url as channel_thumbnail_url, c.country as channel_country,
        COALESCE(vs.processed_count, 0) as processed_count,
        COALESCE(vas.positive_count, 0) as positive_count,
        COALESCE(vas.negative_count, 0) as negative_count,
        COALESCE(vas.neutral_count, 0) as neutral_count
      FROM youtube_videos v
      JOIN youtube_channels c ON v.channel_id = c.id
      LEFT JOIN video_sentiment vs ON vs.video_id = v.id
      LEFT JOIN video_asca_sentiment vas ON vas.video_id = v.id
      ${whereClause}
      ORDER BY COALESCE(vs.processed_count, 0) DESC, v.published_at DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    try {
      const rows = await query<VideoStatsRow>(sql, params);

      // For each video, get detailed stats
      const videosWithStats: YouTubeVideoWithStats[] = await Promise.all(
        rows.map(async (row) => {
          const stats = await this.getVideoDetailedStats(row.id);
          return this.mapToEntityWithStats(row, stats);
        })
      );

      return {
        data: videosWithStats,
        meta: {
          total,
          limit,
          offset,
          hasMore: offset + videosWithStats.length < total,
        },
      };
    } catch (error) {
      console.error("Error fetching videos with stats:", error);
      return {
        data: [],
        meta: { total: 0, limit, offset, hasMore: false },
      };
    }
  }

  /**
   * Get detailed stats for a single video
   */
  async getVideoDetailedStats(videoId: string): Promise<VideoProcessingStats> {
    try {
      // Get total comments and processed count
      const countsSql = `
        SELECT 
          COUNT(DISTINCT yc.id) as total_comments,
          COUNT(DISTINCT CASE WHEN ae.id IS NOT NULL OR i.id IS NOT NULL OR tt.id IS NOT NULL THEN yc.id END) as processed_count
        FROM youtube_comments yc
        LEFT JOIN asca_extractions ae ON ae.source_id = yc.id AND ae.is_deleted = false
        LEFT JOIN intentions i ON i.source_id = yc.id
        LEFT JOIN traveling_types tt ON tt.source_id = yc.id
        WHERE yc.video_id = $1
      `;
      const countsResult = await query<{ total_comments: string; processed_count: string }>(countsSql, [videoId]);

      // Get ASCA sentiment breakdown
      const sentimentSql = `
        SELECT 
          aspect->>'sentiment' as sentiment,
          COUNT(*) as count
        FROM youtube_comments yc
        JOIN asca_extractions ae ON ae.source_id = yc.id AND ae.is_deleted = false,
        jsonb_array_elements(ae.aspects) as aspect
        WHERE yc.video_id = $1
        GROUP BY aspect->>'sentiment'
      `;
      const sentimentResult = await query<{ sentiment: string; count: string }>(sentimentSql, [videoId]);

      // Get top intentions
      const intentionsSql = `
        SELECT i.intention_type as name, COUNT(*) as count
        FROM intentions i
        JOIN youtube_comments yc ON yc.id = i.source_id
        WHERE yc.video_id = $1
        GROUP BY i.intention_type
        ORDER BY count DESC
        LIMIT 5
      `;
      const intentionsResult = await query<{ name: string; count: string }>(intentionsSql, [videoId]);

      // Get top travel types
      const travelTypesSql = `
        SELECT tt.traveling_type as name, COUNT(*) as count
        FROM traveling_types tt
        JOIN youtube_comments yc ON yc.id = tt.source_id
        WHERE yc.video_id = $1
        GROUP BY tt.traveling_type
        ORDER BY count DESC
        LIMIT 5
      `;
      const travelTypesResult = await query<{ name: string; count: string }>(travelTypesSql, [videoId]);

      // Get top locations
      const locationsSql = `
        SELECT loc->>'word' as name, COUNT(*) as count
        FROM location_extractions le,
        jsonb_array_elements(le.locations) as loc
        JOIN youtube_comments yc ON yc.id = le.source_id
        WHERE yc.video_id = $1
        GROUP BY loc->>'word'
        ORDER BY count DESC
        LIMIT 5
      `;
      let locationsResult: { name: string; count: string }[] = [];
      try {
        locationsResult = await query<{ name: string; count: string }>(locationsSql, [videoId]);
      } catch {
        // Table might not exist
      }

      // Get ASCA category breakdown
      const ascaSql = `
        SELECT 
          aspect->>'category' as category,
          COUNT(*) FILTER (WHERE aspect->>'sentiment' = 'positive') as positive,
          COUNT(*) FILTER (WHERE aspect->>'sentiment' = 'negative') as negative,
          COUNT(*) FILTER (WHERE aspect->>'sentiment' = 'neutral') as neutral
        FROM youtube_comments yc
        JOIN asca_extractions ae ON ae.source_id = yc.id AND ae.is_deleted = false,
        jsonb_array_elements(ae.aspects) as aspect
        WHERE yc.video_id = $1
        GROUP BY aspect->>'category'
        ORDER BY (COUNT(*)) DESC
      `;
      let ascaResult: { category: string; positive: string; negative: string; neutral: string }[] = [];
      try {
        ascaResult = await query<{ category: string; positive: string; negative: string; neutral: string }>(ascaSql, [videoId]);
      } catch {
        // Table might not exist
      }

      // Build sentiment breakdown
      const sentiment: SentimentBreakdown = { positive: 0, negative: 0, neutral: 0 };
      for (const row of sentimentResult) {
        if (row.sentiment === 'positive') sentiment.positive = parseInt(row.count, 10);
        else if (row.sentiment === 'negative') sentiment.negative = parseInt(row.count, 10);
        else if (row.sentiment === 'neutral') sentiment.neutral = parseInt(row.count, 10);
      }

      return {
        total_comments: parseInt(countsResult[0]?.total_comments || "0", 10),
        processed_count: parseInt(countsResult[0]?.processed_count || "0", 10),
        sentiment,
        top_intentions: intentionsResult.map(r => ({ name: r.name, count: parseInt(r.count, 10) })),
        top_travel_types: travelTypesResult.map(r => ({ name: r.name, count: parseInt(r.count, 10) })),
        top_locations: locationsResult.map(r => ({ name: r.name, count: parseInt(r.count, 10) })),
        asca_categories: ascaResult.map(r => ({
          category: r.category,
          positive: parseInt(r.positive, 10),
          negative: parseInt(r.negative, 10),
          neutral: parseInt(r.neutral, 10),
        })),
      };
    } catch (error) {
      console.error("Error getting video detailed stats:", error);
      return {
        total_comments: 0,
        processed_count: 0,
        sentiment: { positive: 0, negative: 0, neutral: 0 },
        top_intentions: [],
        top_travel_types: [],
        top_locations: [],
        asca_categories: [],
      };
    }
  }

  /**
   * Get comments for a video with their processing results
   */
  async getCommentsWithStats(
    videoId: string,
    limit = 20,
    offset = 0
  ): Promise<{ data: YouTubeCommentWithStats[]; meta: { total: number; hasMore: boolean } }> {
    try {
      // Count total
      const countSql = `SELECT COUNT(*) as total FROM youtube_comments WHERE video_id = $1`;
      const countResult = await query<{ total: string }>(countSql, [videoId]);
      const total = parseInt(countResult[0]?.total || "0", 10);

      // Get comments with processing data
      const sql = `
        SELECT 
          yc.id, yc.video_id, yc.text, yc.author_display_name, yc.like_count, yc.published_at,
          i.intention_type,
          tt.traveling_type,
          ae.aspects as asca_aspects,
          le.locations as extracted_locations
        FROM youtube_comments yc
        LEFT JOIN intentions i ON i.source_id = yc.id
        LEFT JOIN traveling_types tt ON tt.source_id = yc.id
        LEFT JOIN asca_extractions ae ON ae.source_id = yc.id AND ae.is_deleted = false
        LEFT JOIN location_extractions le ON le.source_id = yc.id
        WHERE yc.video_id = $1
        ORDER BY 
          CASE WHEN ae.id IS NOT NULL OR i.id IS NOT NULL OR tt.id IS NOT NULL THEN 0 ELSE 1 END,
          yc.like_count DESC
        LIMIT $2 OFFSET $3
      `;

      interface CommentRow {
        id: string;
        video_id: string;
        text: string;
        author_display_name: string | null;
        like_count: number;
        published_at: Date;
        intention_type: string | null;
        traveling_type: string | null;
        asca_aspects: unknown;
        extracted_locations: unknown;
      }

      const rows = await query<CommentRow>(sql, [videoId, limit, offset]);

      const data: YouTubeCommentWithStats[] = rows.map(row => {
        // Parse ASCA aspects
        let ascaAspects: Array<{ category: string; sentiment: string }> = [];
        if (row.asca_aspects && Array.isArray(row.asca_aspects)) {
          ascaAspects = (row.asca_aspects as Array<{ category: string; sentiment: string }>).slice(0, 3);
        }

        // Parse locations
        let locations: string[] = [];
        if (row.extracted_locations && Array.isArray(row.extracted_locations)) {
          locations = (row.extracted_locations as Array<{ word: string }>).map(l => l.word).slice(0, 3);
        }

        // Determine overall sentiment from ASCA
        let sentiment: 'positive' | 'negative' | 'neutral' | null = null;
        if (ascaAspects.length > 0) {
          const counts = { positive: 0, negative: 0, neutral: 0 };
          ascaAspects.forEach(a => {
            if (a.sentiment in counts) counts[a.sentiment as keyof typeof counts]++;
          });
          if (counts.positive >= counts.negative && counts.positive >= counts.neutral) sentiment = 'positive';
          else if (counts.negative >= counts.positive && counts.negative >= counts.neutral) sentiment = 'negative';
          else sentiment = 'neutral';
        }

        return {
          id: row.id,
          video_id: row.video_id,
          text: row.text,
          author_name: row.author_display_name,
          like_count: row.like_count || 0,
          published_at: row.published_at,
          processing: {
            sentiment,
            intention: row.intention_type,
            travel_type: row.traveling_type,
            locations,
            asca_aspects: ascaAspects,
          },
        };
      });

      return {
        data,
        meta: { total, hasMore: offset + data.length < total },
      };
    } catch (error) {
      console.error("Error getting comments with stats:", error);
      return { data: [], meta: { total: 0, hasMore: false } };
    }
  }

  private mapToEntityWithStats(row: VideoStatsRow, stats: VideoProcessingStats): YouTubeVideoWithStats {
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
      channel: {
        title: row.channel_title,
        thumbnail_url: row.channel_thumbnail_url,
        country: row.channel_country,
      },
      stats,
    };
  }

  private getTimeRangeCondition(timeRange: string): string | null {
    const timeRangeMap: Record<string, string> = {
      "24h": "v.published_at >= NOW() - INTERVAL '24 hours'",
      "7d": "v.published_at >= NOW() - INTERVAL '7 days'",
      "30d": "v.published_at >= NOW() - INTERVAL '30 days'",
      "90d": "v.published_at >= NOW() - INTERVAL '90 days'",
      "6m": "v.published_at >= NOW() - INTERVAL '6 months'",
      "1y": "v.published_at >= NOW() - INTERVAL '1 year'",
    };
    return timeRangeMap[timeRange] || null;
  }
}

export const videoWithStatsRepository = new VideoWithStatsRepository();
