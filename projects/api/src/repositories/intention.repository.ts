import { query } from "../database/connection";
import {
  IntentionExtraction,
  IntentionType,
} from "../entities/intention.entity";

interface RawIntentionRow {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  intention_type: IntentionType;
  created_at: Date;
}

export class IntentionRepository {
  /**
   * Get all non-deleted intention extractions.
   */
  async findAll(): Promise<IntentionExtraction[]> {
    const sql = `
      SELECT id, source_id, source_type, raw_text, intention_type, created_at
      FROM intentions
     
      
    `;
    const rows = await query<RawIntentionRow>(sql);
    return rows.map((row) => this.mapToEntity(row));
  }

  async findByVideo(id: string): Promise<IntentionExtraction[]> {
    const sql = `
      SELECT i.id, source_id, source_type, raw_text, intention_type, i.created_at, video_id
      FROM intentions i
      JOIN youtube_comments yc ON yc.id = i.source_id
      WHERE yc.video_id = $1
      
    `;
    const rows = await query<RawIntentionRow>(sql, [id]);
    return rows.map((row) => this.mapToEntity(row));
  }

  /**
   * Map database row to entity.
   */
  private mapToEntity(row: RawIntentionRow): IntentionExtraction {
    return {
      id: row.id,
      source_id: row.source_id,
      source_type: row.source_type,
      raw_text: row.raw_text,
      intention_type: row.intention_type,
      created_at: row.created_at.toISOString(),
    };
  }
}

export const intentionRepository = new IntentionRepository();
