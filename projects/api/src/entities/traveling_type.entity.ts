export type TravelingType =
  | "business"
  | "leisure"
  | "adventure"
  | "backpacking"
  | "luxury"
  | "budget"
  | "solo"
  | "group"
  | "family"
  | "romantic"
  | "other";

export interface TravelingTypeExtraction {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  traveling_type: TravelingType;
  created_at: string;
}

export interface TravelingTypeStats {
  name: string;
  value: number;
  color: string;
}