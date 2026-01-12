/**
 * Location entity types matching the simplified NER output schema.
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

// Location Hierarchy Types
export interface ContinentStats {
  id: string;
  name: string;
  count: number;
  countries: string[];
  color: string;
}

export interface CountryStats {
  id: string;
  name: string;
  continent: string;
  count: number;
  regions: string[];
}

export interface RegionStats {
  id: string;
  name: string;
  country: string;
  count: number;
}

export interface LocationHierarchyResponse {
  continents: ContinentStats[];
  total: number;
}

export interface CountryListResponse {
  countries: CountryStats[];
  continent: string;
  total: number;
}

export interface RegionListResponse {
  regions: RegionStats[];
  country: string;
  total: number;
}

