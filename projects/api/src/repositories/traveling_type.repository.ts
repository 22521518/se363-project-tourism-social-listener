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
  async findAll(): Promise<TravelingTypeExtraction[]> {
    const sql = `
      SELECT id, source_id, source_type, raw_text, traveling_type, created_at
      FROM traveling_types
      

    `;
    const rows = await query<RawTravelingTypeRow>(sql);
    return rows.map((row) => this.mapToEntity(row));
  }

  async findByVideo(id: string): Promise<TravelingTypeExtraction[]> {
    const sql = `
      SELECT t.id, source_id, source_type, raw_text, traveling_type, t.created_at
      FROM traveling_types t
      JOIN youtube_comments yc ON yc.id = t.source_id
      WHERE video_id = $1
     

    `;
    const rows = await query<RawTravelingTypeRow>(sql, [id]);
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
      created_at: new Date(row.created_at).toISOString(),
    };
  }
}

export const travelingTypeRepository = new TravelingTypeRepository();
