import { query } from "../database/connection";
import {
  TravelingTypeExtraction,
  TravelingType,
} from "../entities/traveling_type.entity";

interface RawTravelingTypeRow {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  traveling_type: TravelingType;
  created_at: Date;
}

export class TravelingTypeRepository {
  /**
   * Get all traveling type extractions.
   */
  async findAll(limit = 100, offset = 0): Promise<TravelingTypeExtraction[]> {
    const sql = `
      SELECT id, source_id, source_type, raw_text, traveling_type, created_at
      FROM traveling_types
      ORDER BY created_at DESC
      LIMIT $1 OFFSET $2
    `;
    const rows = await query<RawTravelingTypeRow>(sql, [limit, offset]);
    return rows.map((row) => this.mapToEntity(row));
  }

  /**
   * Map database row to entity.
   */
  private mapToEntity(row: RawTravelingTypeRow): TravelingTypeExtraction {
    return {
      id: row.id,
      source_id: row.source_id,
      source_type: row.source_type,
      raw_text: row.raw_text,
      traveling_type: row.traveling_type,
      created_at: row.created_at.toISOString(),
    };
  }
}

export const travelingTypeRepository = new TravelingTypeRepository();