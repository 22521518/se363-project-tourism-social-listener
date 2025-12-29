import { query } from '../database/connection';
import { LocationExtraction, Location, ApprovedResult } from '../entities/location.entity';

interface RawLocationRow {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  locations: Location[];
  primary_location: { name: string; confidence: number } | null;
  overall_score: number;
  is_approved: boolean;
  approved_result: ApprovedResult | null;
  is_deleted: boolean;
  created_at: Date;
}

export class LocationRepository {
  /**
   * Get all non-deleted location extractions.
   * Returns the effective result (approved_result if approved, otherwise original).
   */
  async findAll(limit = 100, offset = 0): Promise<LocationExtraction[]> {
    const sql = `
      SELECT id, source_id, source_type, raw_text, locations, 
             primary_location, overall_score, is_approved, approved_result, created_at
      FROM location_extractions
      WHERE is_deleted = false
      ORDER BY created_at DESC
      LIMIT $1 OFFSET $2
    `;
    const rows = await query<RawLocationRow>(sql, [limit, offset]);
    return rows.map(row => this.mapToEntity(row));
  }

  /**
   * Get all unique locations with their types.
   * Uses approved_result.locations if approved, otherwise original locations.
   */
  async findAllLocationsFlat(): Promise<Location[]> {
    const sql = `
      SELECT locations, is_approved, approved_result
      FROM location_extractions
      WHERE is_deleted = false AND (locations IS NOT NULL OR approved_result IS NOT NULL)
    `;
    const rows = await query<{ locations: Location[]; is_approved: boolean; approved_result: ApprovedResult | null }>(sql);

    const allLocations: Location[] = [];
    for (const row of rows) {
      // Use approved_result if approved and available, otherwise fallback to original
      const effectiveLocations = (row.is_approved && row.approved_result?.locations)
        ? row.approved_result.locations
        : row.locations;

      if (Array.isArray(effectiveLocations)) {
        allLocations.push(...effectiveLocations);
      }
    }
    return allLocations;
  }

  /**
   * Map database row to entity.
   * If is_approved is true and approved_result exists, use approved data.
   */
  private mapToEntity(row: RawLocationRow): LocationExtraction {
    // Determine effective values based on approval status
    const useApproved = row.is_approved && row.approved_result;

    const effectiveLocations = useApproved && row.approved_result?.locations
      ? row.approved_result.locations
      : (row.locations || []);

    const effectivePrimaryLocation = useApproved && row.approved_result?.primary_location !== undefined
      ? row.approved_result.primary_location
      : row.primary_location;

    const effectiveScore = useApproved && row.approved_result?.overall_score !== undefined
      ? row.approved_result.overall_score
      : row.overall_score;

    return {
      id: row.id,
      source_id: row.source_id,
      source_type: row.source_type,
      raw_text: row.raw_text,
      locations: effectiveLocations,
      primary_location: effectivePrimaryLocation,
      overall_score: effectiveScore,
      is_approved: row.is_approved,
      approved_result: row.approved_result,
      created_at: row.created_at.toISOString(),
    };
  }
}

export const locationRepository = new LocationRepository();
