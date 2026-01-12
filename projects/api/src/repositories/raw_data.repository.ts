import { query } from '../database/connection';
import {
  RawDataItem,
  RawDataListResponse,
  ProcessingStatus,
  ProcessingTask,
  ProcessingFilter,
  SourceType,
  YouTubeCommentMetadata,
  WebCrawlMetadata,
} from '../entities/raw_data.entity';

interface YouTubeCommentRow {
  id: string;
  text: string;
  video_id: string;
  video_title: string | null;
  channel_title: string | null;
  author_display_name: string | null;
  like_count: number;
  published_at: Date;
  created_at: Date;
  has_asca: boolean;
  has_intention: boolean;
  has_location: boolean;
  has_traveling_type: boolean;
}

interface WebCrawlRow {
  id: string;
  request_id: string;
  url: string;
  title: string | null;
  content_type: string;
  information: string | null;
  crawl_time: Date;
  has_asca: boolean;
  has_intention: boolean;
  has_location: boolean;
  has_traveling_type: boolean;
}

export class RawDataRepository {
  /**
   * Get YouTube comments with processing status
   */
  async findYouTubeComments(
    limit = 20,
    offset = 0,
    processingFilter: ProcessingFilter = 'all',
    task: ProcessingTask | 'all' = 'all'
  ): Promise<RawDataListResponse> {
    const params: unknown[] = [];
    const conditions: string[] = [];

    // Build processing filter conditions
    const filterCondition = this.buildProcessingFilterCondition(
      processingFilter,
      task,
      'yc.id'
    );
    if (filterCondition) {
      conditions.push(filterCondition);
    }

    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

    // Count total
    const countSql = `
      SELECT COUNT(DISTINCT yc.id) as total
      FROM youtube_comments yc
      LEFT JOIN youtube_videos v ON v.id = yc.video_id
      LEFT JOIN youtube_channels c ON c.id = v.channel_id
      ${whereClause}
    `;
    const countResult = await query<{ total: string }>(countSql, params);
    const total = parseInt(countResult[0]?.total || '0', 10);

    // Get processed counts
    const summary = await this.getYouTubeProcessingSummary();

    // Main query - add limit/offset params
    params.push(limit, offset);

    // Build ORDER BY clause - prioritize processed items for selected task
    let orderByClause = 'ORDER BY ';
    if (task !== 'all') {
      const taskOrderMap: Record<ProcessingTask, string> = {
        asca: 'CASE WHEN ae.id IS NOT NULL THEN 0 ELSE 1 END',
        intention: 'CASE WHEN i.id IS NOT NULL THEN 0 ELSE 1 END',
        location_extraction: 'CASE WHEN le.id IS NOT NULL THEN 0 ELSE 1 END',
        traveling_type: 'CASE WHEN tt.id IS NOT NULL THEN 0 ELSE 1 END',
      };
      orderByClause += `${taskOrderMap[task]}, `;
    }
    orderByClause += 'yc.published_at DESC';

    const sql = `
      SELECT 
        yc.id,
        yc.text,
        yc.video_id,
        v.title as video_title,
        c.title as channel_title,
        yc.author_display_name,
        yc.like_count,
        yc.published_at,
        yc.created_at,
        CASE WHEN ae.id IS NOT NULL THEN true ELSE false END as has_asca,
        CASE WHEN i.id IS NOT NULL THEN true ELSE false END as has_intention,
        CASE WHEN le.id IS NOT NULL THEN true ELSE false END as has_location,
        CASE WHEN tt.id IS NOT NULL THEN true ELSE false END as has_traveling_type
      FROM youtube_comments yc
      LEFT JOIN youtube_videos v ON v.id = yc.video_id
      LEFT JOIN youtube_channels c ON c.id = v.channel_id
      LEFT JOIN asca_extractions ae ON ae.source_id = yc.id AND ae.is_deleted = false
      LEFT JOIN intentions i ON i.source_id = yc.id
      LEFT JOIN location_extractions le ON le.source_id = yc.id
      LEFT JOIN traveling_types tt ON tt.source_id = yc.id
      ${whereClause}
      ${orderByClause}
      LIMIT $1 OFFSET $2
    `;

    const rows = await query<YouTubeCommentRow>(sql, params);

    const data: RawDataItem[] = rows.map(row => ({
      id: row.id,
      source_type: 'youtube_comment' as SourceType,
      text: row.text,
      metadata: {
        video_id: row.video_id,
        video_title: row.video_title || undefined,
        channel_title: row.channel_title || undefined,
        author_name: row.author_display_name,
        like_count: row.like_count || 0,
        published_at: row.published_at,
      } as YouTubeCommentMetadata,
      processing_status: {
        asca: row.has_asca,
        intention: row.has_intention,
        location_extraction: row.has_location,
        traveling_type: row.has_traveling_type,
      },
      created_at: row.created_at,
    }));

    return {
      data,
      meta: {
        total,
        limit,
        offset,
        hasMore: offset + data.length < total,
      },
      summary,
    };
  }

  /**
   * Get WebCrawl data with processing status
   */
  async findWebCrawlData(
    limit = 20,
    offset = 0,
    processingFilter: ProcessingFilter = 'all',
    task: ProcessingTask | 'all' = 'all'
  ): Promise<RawDataListResponse> {
    const emptyResponse: RawDataListResponse = {
      data: [],
      meta: { total: 0, limit, offset, hasMore: false },
      summary: {
        total_items: 0,
        processed_counts: { asca: 0, intention: 0, location_extraction: 0, traveling_type: 0 },
      },
    };

    try {
      const params: unknown[] = [];
      const conditions: string[] = [];

      // Build processing filter conditions
      const filterCondition = this.buildProcessingFilterCondition(
        processingFilter,
        task,
        'ch.request_id'
      );
      if (filterCondition) {
        conditions.push(filterCondition);
      }

      const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

      // Count total
      const countSql = `
        SELECT COUNT(DISTINCT ch.id) as total
        FROM crawl_history ch
        LEFT JOIN crawl_result cr ON cr.crawl_history_id = ch.id
        ${whereClause}
      `;
      const countResult = await query<{ total: string }>(countSql, params);
      const total = parseInt(countResult[0]?.total || '0', 10);

      // Get processed counts
      const summary = await this.getWebCrawlProcessingSummary();

      // Main query - add limit/offset params
      params.push(limit, offset);

      // Build ORDER BY clause - prioritize processed items for selected task
      let orderByClause = 'ORDER BY ';
      if (task !== 'all') {
        const taskOrderMap: Record<ProcessingTask, string> = {
          asca: 'CASE WHEN ae.id IS NOT NULL THEN 0 ELSE 1 END',
          intention: 'CASE WHEN i.id IS NOT NULL THEN 0 ELSE 1 END',
          location_extraction: 'CASE WHEN le.id IS NOT NULL THEN 0 ELSE 1 END',
          traveling_type: 'CASE WHEN tt.id IS NOT NULL THEN 0 ELSE 1 END',
        };
        orderByClause += `${taskOrderMap[task]}, `;
      }
      orderByClause += 'ch.crawl_time DESC';

      const sql = `
        SELECT 
          ch.id::text,
          ch.request_id,
          ch.url,
          cr.title,
          ch.content_type,
          cr.information,
          ch.crawl_time,
          CASE WHEN ae.id IS NOT NULL THEN true ELSE false END as has_asca,
          CASE WHEN i.id IS NOT NULL THEN true ELSE false END as has_intention,
          CASE WHEN le.id IS NOT NULL THEN true ELSE false END as has_location,
          CASE WHEN tt.id IS NOT NULL THEN true ELSE false END as has_traveling_type
        FROM crawl_history ch
        LEFT JOIN crawl_result cr ON cr.crawl_history_id = ch.id
        LEFT JOIN asca_extractions ae ON ae.source_id = ch.request_id AND ae.is_deleted = false
        LEFT JOIN intentions i ON i.source_id = ch.request_id
        LEFT JOIN location_extractions le ON le.source_id = ch.request_id
        LEFT JOIN traveling_types tt ON tt.source_id = ch.request_id
        ${whereClause}
        ${orderByClause}
        LIMIT $1 OFFSET $2
      `;

      const rows = await query<WebCrawlRow>(sql, params);

      const data: RawDataItem[] = rows.map(row => ({
        id: row.request_id,
        source_type: 'webcrawl' as SourceType,
        text: row.information || '',
        metadata: {
          url: row.url,
          title: row.title,
          content_type: row.content_type,
          crawl_time: row.crawl_time,
        } as WebCrawlMetadata,
        processing_status: {
          asca: row.has_asca,
          intention: row.has_intention,
          location_extraction: row.has_location,
          traveling_type: row.has_traveling_type,
        },
        created_at: row.crawl_time,
      }));

      return {
        data,
        meta: {
          total,
          limit,
          offset,
          hasMore: offset + data.length < total,
        },
        summary,
      };
    } catch (error: unknown) {
      // Handle missing table gracefully (e.g., crawl_history doesn't exist)
      const pgError = error as { code?: string };
      if (pgError.code === '42P01') {
        console.warn('WebCrawl tables not found, returning empty data');
        return emptyResponse;
      }
      throw error;
    }
  }

  /**
   * Get processing summary for YouTube comments
   */
  private async getYouTubeProcessingSummary(): Promise<RawDataListResponse['summary']> {
    const sql = `
      SELECT 
        COUNT(DISTINCT yc.id) as total_items,
        COUNT(DISTINCT ae.source_id) as asca_count,
        COUNT(DISTINCT i.source_id) as intention_count,
        COUNT(DISTINCT le.source_id) as location_count,
        COUNT(DISTINCT tt.source_id) as traveling_type_count
      FROM youtube_comments yc
      LEFT JOIN asca_extractions ae ON ae.source_id = yc.id AND ae.is_deleted = false
      LEFT JOIN intentions i ON i.source_id = yc.id
      LEFT JOIN location_extractions le ON le.source_id = yc.id
      LEFT JOIN traveling_types tt ON tt.source_id = yc.id
    `;
    const result = await query<{
      total_items: string;
      asca_count: string;
      intention_count: string;
      location_count: string;
      traveling_type_count: string;
    }>(sql);

    return {
      total_items: parseInt(result[0]?.total_items || '0', 10),
      processed_counts: {
        asca: parseInt(result[0]?.asca_count || '0', 10),
        intention: parseInt(result[0]?.intention_count || '0', 10),
        location_extraction: parseInt(result[0]?.location_count || '0', 10),
        traveling_type: parseInt(result[0]?.traveling_type_count || '0', 10),
      },
    };
  }

  /**
   * Get processing summary for WebCrawl data
   */
  private async getWebCrawlProcessingSummary(): Promise<RawDataListResponse['summary']> {
    const emptyResult = {
      total_items: 0,
      processed_counts: { asca: 0, intention: 0, location_extraction: 0, traveling_type: 0 },
    };

    try {
      const sql = `
        SELECT 
          COUNT(DISTINCT ch.id) as total_items,
          COUNT(DISTINCT ae.source_id) as asca_count,
          COUNT(DISTINCT i.source_id) as intention_count,
          COUNT(DISTINCT le.source_id) as location_count,
          COUNT(DISTINCT tt.source_id) as traveling_type_count
        FROM crawl_history ch
        LEFT JOIN asca_extractions ae ON ae.source_id = ch.request_id AND ae.is_deleted = false
        LEFT JOIN intentions i ON i.source_id = ch.request_id
        LEFT JOIN location_extractions le ON le.source_id = ch.request_id
        LEFT JOIN traveling_types tt ON tt.source_id = ch.request_id
      `;
      const result = await query<{
        total_items: string;
        asca_count: string;
        intention_count: string;
        location_count: string;
        traveling_type_count: string;
      }>(sql);

      return {
        total_items: parseInt(result[0]?.total_items || '0', 10),
        processed_counts: {
          asca: parseInt(result[0]?.asca_count || '0', 10),
          intention: parseInt(result[0]?.intention_count || '0', 10),
          location_extraction: parseInt(result[0]?.location_count || '0', 10),
          traveling_type: parseInt(result[0]?.traveling_type_count || '0', 10),
        },
      };
    } catch (error: unknown) {
      const pgError = error as { code?: string };
      if (pgError.code === '42P01') {
        return emptyResult;
      }
      throw error;
    }
  }

  /**
   * Build SQL condition for processing filter
   */
  private buildProcessingFilterCondition(
    processingFilter: ProcessingFilter,
    task: ProcessingTask | 'all',
    sourceIdColumn: string
  ): string | null {
    if (processingFilter === 'all') return null;

    const taskTables: Record<ProcessingTask, { table: string; sourceCol: string }> = {
      asca: { table: 'asca_extractions', sourceCol: 'source_id' },
      intention: { table: 'intentions', sourceCol: 'source_id' },
      location_extraction: { table: 'location_extractions', sourceCol: 'source_id' },
      traveling_type: { table: 'traveling_types', sourceCol: 'source_id' },
    };

    if (task !== 'all') {
      const { table, sourceCol } = taskTables[task];
      const existsCheck = `EXISTS (SELECT 1 FROM ${table} WHERE ${sourceCol} = ${sourceIdColumn}${task === 'asca' ? ' AND is_deleted = false' : ''})`;
      return processingFilter === 'processed' ? existsCheck : `NOT ${existsCheck}`;
    }

    // For 'all' tasks with processing filter
    const allTasks = Object.entries(taskTables);
    if (processingFilter === 'processed') {
      // Has at least one processing result
      const checks = allTasks.map(([taskName, { table, sourceCol }]) => {
        const extra = taskName === 'asca' ? ' AND is_deleted = false' : '';
        return `EXISTS (SELECT 1 FROM ${table} WHERE ${sourceCol} = ${sourceIdColumn}${extra})`;
      });
      return `(${checks.join(' OR ')})`;
    } else {
      // Has no processing results at all
      const checks = allTasks.map(([taskName, { table, sourceCol }]) => {
        const extra = taskName === 'asca' ? ' AND is_deleted = false' : '';
        return `NOT EXISTS (SELECT 1 FROM ${table} WHERE ${sourceCol} = ${sourceIdColumn}${extra})`;
      });
      return `(${checks.join(' AND ')})`;
    }
  }

  /**
   * Get processing details for a specific source item by ID
   */
  async getProcessingDetails(sourceId: string): Promise<{
    asca: { processed: boolean; aspects: Array<{ category: string; sentiment: string; confidence: number }> };
    intention: { processed: boolean; intention_type: string | null };
    location_extraction: { processed: boolean; locations: Array<{ word: string; entity_group: string; score: number }> };
    traveling_type: { processed: boolean; traveling_type: string | null };
  }> {
    // Fetch ASCA aspects
    const ascaSql = `
      SELECT aspects 
      FROM asca_extractions 
      WHERE source_id = $1 AND is_deleted = false 
      LIMIT 1
    `;
    const ascaRows = await query<{ aspects: string }>(ascaSql, [sourceId]);
    const ascaAspects = ascaRows.length > 0
      ? (typeof ascaRows[0].aspects === 'string' ? JSON.parse(ascaRows[0].aspects) : ascaRows[0].aspects)
      : [];

    // Fetch Intention
    const intentionSql = `
      SELECT intention_type 
      FROM intentions 
      WHERE source_id = $1 
      LIMIT 1
    `;
    const intentionRows = await query<{ intention_type: string }>(intentionSql, [sourceId]);

    // Fetch Locations
    const locationSql = `
      SELECT locations 
      FROM location_extractions 
      WHERE source_id = $1 
      LIMIT 1
    `;
    const locationRows = await query<{ locations: unknown }>(locationSql, [sourceId]);
    const locations = locationRows.length > 0
      ? (Array.isArray(locationRows[0].locations)
        ? locationRows[0].locations
        : (typeof locationRows[0].locations === 'string'
          ? JSON.parse(locationRows[0].locations as string)
          : []))
      : [];

    // Fetch Traveling Type
    const travelingSql = `
      SELECT traveling_type 
      FROM traveling_types 
      WHERE source_id = $1 
      LIMIT 1
    `;
    const travelingRows = await query<{ traveling_type: string }>(travelingSql, [sourceId]);

    return {
      asca: {
        processed: ascaRows.length > 0,
        aspects: ascaAspects.map((a: { category?: string; sentiment?: string; confidence?: number }) => ({
          category: a.category || 'unknown',
          sentiment: a.sentiment || 'neutral',
          confidence: a.confidence || 0,
        })),
      },
      intention: {
        processed: intentionRows.length > 0,
        intention_type: intentionRows.length > 0 ? intentionRows[0].intention_type : null,
      },
      location_extraction: {
        processed: locationRows.length > 0,
        locations: locations.map((l: { word?: string; entity_group?: string; score?: number }) => ({
          word: l.word || '',
          entity_group: l.entity_group || 'LOC',
          score: l.score || 0,
        })),
      },
      traveling_type: {
        processed: travelingRows.length > 0,
        traveling_type: travelingRows.length > 0 ? travelingRows[0].traveling_type : null,
      },
    };
  }
}

export const rawDataRepository = new RawDataRepository();
