import { query } from "../database/connection";
import {
  ASCAExtraction,
  ASCACategoryStats,
  CategoryType,
  SentimentType,
} from "../entities/asca.entity";

interface RawASCARow {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  aspects: string; // JSONB stored as string
  overall_score: number;
  meta: string; // JSONB stored as string
  is_approved: boolean;
  approved_result: string | null;
  is_deleted: boolean;
  created_at: Date;
  updated_at: Date;
}

interface AspectRow {
  category: CategoryType;
  sentiment: SentimentType;
  confidence: number;
}

export class ASCARepository {
  /**
   * Get all non-deleted ASCA extractions.
   */
  async findAll(limit: number = 100, offset: number = 0): Promise<ASCAExtraction[]> {
    const sql = `
      SELECT id, source_id, source_type, raw_text, aspects, overall_score, 
             meta, is_approved, approved_result, is_deleted, created_at, updated_at
      FROM asca_extractions
      WHERE is_deleted = false
      ORDER BY created_at DESC
      LIMIT $1 OFFSET $2
    `;
    const rows = await query<RawASCARow>(sql, [limit, offset]);
    return rows.map((row) => this.mapToEntity(row));
  }

  /**
   * Get ASCA extractions by video ID (via source_id join with comments).
   */
  async findByVideoId(videoId: string): Promise<ASCAExtraction[]> {
    const sql = `
      SELECT a.id, a.source_id, a.source_type, a.raw_text, a.aspects, 
             a.overall_score, a.meta, a.is_approved, a.approved_result, 
             a.is_deleted, a.created_at, a.updated_at
      FROM asca_extractions a
      JOIN youtube_comments yc ON yc.id = a.source_id
      WHERE yc.video_id = $1 AND a.is_deleted = false
      ORDER BY a.created_at DESC
    `;
    const rows = await query<RawASCARow>(sql, [videoId]);
    return rows.map((row) => this.mapToEntity(row));
  }

  /**
   * Get aggregated stats by category.
   */
  async getCategoryStats(): Promise<ASCACategoryStats[]> {
    // This query unnests the aspects JSONB array and aggregates by category and sentiment
    const sql = `
      SELECT 
        aspect->>'category' as category,
        aspect->>'sentiment' as sentiment,
        COUNT(*) as count
      FROM asca_extractions,
           jsonb_array_elements(aspects) as aspect
      WHERE is_deleted = false
      GROUP BY aspect->>'category', aspect->>'sentiment'
      ORDER BY category, sentiment
    `;

    interface CategorySentimentRow {
      category: CategoryType;
      sentiment: SentimentType;
      count: string;
    }

    const rows = await query<CategorySentimentRow>(sql);

    // Aggregate into category stats
    const categoriesMap = new Map<CategoryType, ASCACategoryStats>();

    for (const row of rows) {
      const category = row.category;
      if (!categoriesMap.has(category)) {
        categoriesMap.set(category, {
          category,
          positive: 0,
          negative: 0,
          neutral: 0,
          total: 0,
        });
      }

      const stats = categoriesMap.get(category)!;
      const count = parseInt(row.count, 10);

      switch (row.sentiment) {
        case 'positive':
          stats.positive = count;
          break;
        case 'negative':
          stats.negative = count;
          break;
        case 'neutral':
          stats.neutral = count;
          break;
      }
      stats.total += count;
    }

    return Array.from(categoriesMap.values());
  }

  /**
   * Get aggregated stats by category for a specific video.
   */
  async getCategoryStatsByVideoId(videoId: string): Promise<ASCACategoryStats[]> {
    const sql = `
      SELECT 
        aspect->>'category' as category,
        aspect->>'sentiment' as sentiment,
        COUNT(*) as count
      FROM asca_extractions a
      JOIN youtube_comments yc ON yc.id = a.source_id,
           jsonb_array_elements(a.aspects) as aspect
      WHERE a.is_deleted = false AND yc.video_id = $1
      GROUP BY aspect->>'category', aspect->>'sentiment'
      ORDER BY category, sentiment
    `;

    interface CategorySentimentRow {
      category: CategoryType;
      sentiment: SentimentType;
      count: string;
    }

    const rows = await query<CategorySentimentRow>(sql, [videoId]);

    const categoriesMap = new Map<CategoryType, ASCACategoryStats>();

    for (const row of rows) {
      const category = row.category;
      if (!categoriesMap.has(category)) {
        categoriesMap.set(category, {
          category,
          positive: 0,
          negative: 0,
          neutral: 0,
          total: 0,
        });
      }

      const stats = categoriesMap.get(category)!;
      const count = parseInt(row.count, 10);

      switch (row.sentiment) {
        case 'positive':
          stats.positive = count;
          break;
        case 'negative':
          stats.negative = count;
          break;
        case 'neutral':
          stats.neutral = count;
          break;
      }
      stats.total += count;
    }

    return Array.from(categoriesMap.values());
  }

  /**
   * Get total counts.
   */
  async getTotalCounts(): Promise<{ total: number; approved: number; pending: number }> {
    const sql = `
      SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE is_approved = true) as approved,
        COUNT(*) FILTER (WHERE is_approved = false) as pending
      FROM asca_extractions
      WHERE is_deleted = false
    `;

    interface CountRow {
      total: string;
      approved: string;
      pending: string;
    }

    const rows = await query<CountRow>(sql);
    const row = rows[0] || { total: '0', approved: '0', pending: '0' };

    return {
      total: parseInt(row.total, 10),
      approved: parseInt(row.approved, 10),
      pending: parseInt(row.pending, 10),
    };
  }

  /**
   * Map database row to entity.
   */
  private mapToEntity(row: RawASCARow): ASCAExtraction {
    return {
      id: row.id,
      source_id: row.source_id,
      source_type: row.source_type,
      raw_text: row.raw_text,
      aspects: typeof row.aspects === 'string' ? JSON.parse(row.aspects) : row.aspects,
      overall_score: row.overall_score,
      meta: typeof row.meta === 'string' ? JSON.parse(row.meta) : (row.meta || {}),
      is_approved: row.is_approved,
      approved_result: row.approved_result
        ? (typeof row.approved_result === 'string' ? JSON.parse(row.approved_result) : row.approved_result)
        : null,
      is_deleted: row.is_deleted,
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }
}

export const ascaRepository = new ASCARepository();
