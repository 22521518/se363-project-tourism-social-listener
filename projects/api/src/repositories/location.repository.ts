import { query } from '../database/connection';
import { LocationExtraction, Location } from '../entities/location.entity';

interface RawLocationRow {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  locations: Location[];
  primary_location: { name: string; confidence: number } | null;
  overall_score: number;
  is_approved: boolean;
  is_deleted: boolean;
  created_at: Date;
}

export class LocationRepository {
  /**
   * Get all non-deleted location extractions.
   */
  async findAll(limit = 100, offset = 0): Promise<LocationExtraction[]> {
    const sql = `
      SELECT id, source_id, source_type, raw_text, locations, 
             primary_location, overall_score, is_approved, created_at
      FROM location_extractions
      WHERE is_deleted = false
      ORDER BY created_at DESC
      LIMIT $1 OFFSET $2
    `;
    const rows = await query<RawLocationRow>(sql, [limit, offset]);
    return rows.map(this.mapToEntity);
  }

  /**
   * Get all unique locations with their types.
   */
  async findAllLocationsFlat(): Promise<Location[]> {
    const sql = `
      SELECT locations
      FROM location_extractions
      WHERE is_deleted = false AND locations IS NOT NULL
    `;
    const rows = await query<{ locations: Location[] }>(sql);

    const allLocations: Location[] = [];
    for (const row of rows) {
      if (Array.isArray(row.locations)) {
        allLocations.push(...row.locations);
      }
    }
    return allLocations;
  }

  private mapToEntity(row: RawLocationRow): LocationExtraction {
    return {
      id: row.id,
      source_id: row.source_id,
      source_type: row.source_type,
      raw_text: row.raw_text,
      locations: row.locations || [],
      primary_location: row.primary_location,
      overall_score: row.overall_score,
      is_approved: row.is_approved,
      created_at: row.created_at.toISOString(),
    };
  }
}

export const locationRepository = new LocationRepository();
