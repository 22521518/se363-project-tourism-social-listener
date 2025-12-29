/**
 * Location entity types matching the database schema.
 */

export type LocationType = 'country' | 'city' | 'state' | 'province' | 'landmark' | 'unknown';

export interface Location {
  name: string;
  type: LocationType;
  confidence: number;
}

export interface PrimaryLocation {
  name: string;
  confidence: number;
}

export interface LocationExtraction {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  locations: Location[];
  primary_location: PrimaryLocation | null;
  overall_score: number;
  is_approved: boolean;
  created_at: string;
}

export interface GeographyStats {
  name: string;
  value: number;
  color: string;
}
