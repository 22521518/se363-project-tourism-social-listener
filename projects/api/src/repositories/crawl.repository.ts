import { query } from "../database/connection";
import {
  CrawlResultWithHistory,
  ContentType,
  CrawlContent,
  CrawlMeta,
} from "../entities/crawl.entity";

interface RawCrawlResultRow {
  id: number;
  crawl_history_id: number;
  title: string | null;
  information: string | null;
  language: string | null;
  reviews_json: unknown;
  comments_json: unknown;
  blog_sections_json: unknown;
  agency_info_json: unknown | null;
  detected_sections: string[];
  crawl_strategy: string;
  extraction_strategy: string;
  url: string;
  content_type: ContentType;
  status: string;
  crawl_time: Date;
  request_id: string;
}

export class CrawlRepository {
  /**
   * Get all crawl results with history info.
   */
  async findAll(
    limit: number = 100,
    offset: number = 0,
    contentType?: ContentType
  ): Promise<CrawlResultWithHistory[]> {
    let sql = `
      SELECT 
        cr.id, cr.crawl_history_id, cr.title, cr.information, cr.language,
        cr.reviews_json, cr.comments_json, cr.blog_sections_json,
        cr.agency_info_json, cr.detected_sections, cr.crawl_strategy,
        cr.extraction_strategy, 
        ch.url, ch.content_type, ch.status, ch.crawl_time, ch.request_id
      FROM crawl_result cr
      JOIN crawl_history ch ON ch.id = cr.crawl_history_id
      WHERE ch.status = 'completed'
    `;

    const params: unknown[] = [];

    if (contentType) {
      sql += ` AND ch.content_type = $${params.length + 1}`;
      params.push(contentType);
    }

    sql += ` ORDER BY ch.crawl_time DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    params.push(limit, offset);

    const rows = await query<RawCrawlResultRow>(sql, params);
    return rows.map((row) => this.mapToEntityWithHistory(row));
  }

  /**
   * Get total count of crawl results.
   */
  async getCount(contentType?: ContentType): Promise<number> {
    let sql = `
      SELECT COUNT(*) as count
      FROM crawl_result cr
      JOIN crawl_history ch ON ch.id = cr.crawl_history_id
      WHERE ch.status = 'completed'
    `;

    const params: unknown[] = [];

    if (contentType) {
      sql += ` AND ch.content_type = $1`;
      params.push(contentType);
    }

    interface CountRow { count: string }
    const rows = await query<CountRow>(sql, params);

    return parseInt(rows[0]?.count || '0', 10);
  }

  /**
   * Get crawl stats by content type.
   */
  async getStatsByContentType(): Promise<Record<ContentType, number>> {
    const sql = `
      SELECT ch.content_type, COUNT(*) as count
      FROM crawl_result cr
      JOIN crawl_history ch ON ch.id = cr.crawl_history_id
      WHERE ch.status = 'completed'
      GROUP BY ch.content_type
    `;

    interface StatsRow {
      content_type: ContentType;
      count: string;
    }

    const rows = await query<StatsRow>(sql);

    const stats: Record<ContentType, number> = {
      forum: 0,
      review: 0,
      blog: 0,
      agency: 0,
      auto: 0,
    };

    for (const row of rows) {
      stats[row.content_type] = parseInt(row.count, 10);
    }

    return stats;
  }

  /**
   * Map database row to entity with history.
   */
  private mapToEntityWithHistory(row: RawCrawlResultRow): CrawlResultWithHistory {
    const parseJson = <T>(value: unknown): T => {
      if (typeof value === 'string') {
        try {
          return JSON.parse(value);
        } catch {
          return [] as unknown as T;
        }
      }
      return (value || []) as T;
    };

    const content: CrawlContent = {
      title: row.title,
      information: row.information,
      reviews: parseJson(row.reviews_json) || [],
      comments: parseJson(row.comments_json) || [],
      blog_sections: parseJson(row.blog_sections_json) || [],
      agency_info: row.agency_info_json ? parseJson(row.agency_info_json) : null,
    };

    const meta: CrawlMeta = {
      crawl_time: row.crawl_time,
      language: row.language,
      crawl_strategy: row.crawl_strategy as 'single' | 'deep',
      extraction_strategy: row.extraction_strategy as 'css' | 'llm',
      detected_sections: row.detected_sections || [],
    };

    return {
      id: row.id.toString(),
      request_id: row.request_id || row.crawl_history_id.toString(),
      url: row.url || '',
      content_type: row.content_type || 'auto',
      from_cache: false,
      meta,
      content,
      created_at: row.crawl_time,
    };
  }
}

export const crawlRepository = new CrawlRepository();
