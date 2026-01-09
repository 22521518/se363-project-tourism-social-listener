import { query } from '../database/connection';
import { LocationExtraction, Location } from '../entities/location.entity';

interface RawLocationRow {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  locations: Location[];
  created_at: Date;
}

export class LocationRepository {
  /**
   * Get all location extractions.
   */
  async findAll(limit = 100, offset = 0): Promise<LocationExtraction[]> {
    const sql = `
      SELECT id, source_id, source_type, raw_text, locations, created_at
      FROM location_extractions
      ORDER BY created_at DESC
      LIMIT $1 OFFSET $2
    `;
    const rows = await query<RawLocationRow>(sql, [limit, offset]);
    return rows.map(row => this.mapToEntity(row));
  }

  /**
   * Get all locations as flat list.
   */
  async findAllLocationsFlat(): Promise<Location[]> {
    const sql = `
      SELECT locations
      FROM location_extractions
      WHERE locations IS NOT NULL
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

  /**
   * Map database row to entity.
   */
  private mapToEntity(row: RawLocationRow): LocationExtraction {
    return {
      id: row.id,
      source_id: row.source_id,
      source_type: row.source_type,
      raw_text: row.raw_text,
      locations: row.locations || [],
      created_at: row.created_at.toISOString(),
    };
  }
}

export const locationRepository = new LocationRepository();
