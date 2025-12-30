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
  async findAll(limit = 100, offset = 0): Promise<IntentionExtraction[]> {
    const sql = `
      SELECT id, source_id, source_type, raw_text, intention_type, created_at
      FROM intentions
      ORDER BY created_at DESC
      LIMIT $1 OFFSET $2
    `;
    const rows = await query<RawIntentionRow>(sql, [limit, offset]);
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
