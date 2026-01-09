/**
 * Location-related types for the frontend (simplified NER output).
 */

export interface Location {
  word: string;
  score: number;
  entity_group: string;
  start: number;
  end: number;
}

export interface LocationExtraction {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  locations: Location[];
  created_at: string;
}

export interface GeographyStats {
  name: string;
  value: number;
  color: string;
}
