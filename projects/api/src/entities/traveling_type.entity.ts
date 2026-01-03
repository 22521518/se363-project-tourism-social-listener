export type TravelingType =
  | "BUSINESS"
  | "LEISURE"
  | "ADVENTURE"
  | "BACKPACKING"
  | "LUXURY"
  | "BUDGET"
  | "SOLO"
  | "GROUP"
  | "FAMILY"
  | "ROMANTIC"
  | "OTHER";

export const CATEGORY_COLORS: Record<TravelingType, string> = {
  BUSINESS: "#3b82f6", // Blue - Business
  LEISURE: "#10b981", // Green - Leisure
  ADVENTURE: "#f59e0b", // Orange - Adventure
  BACKPACKING: "#8b5cf6", // Purple - Backpacking
  LUXURY: "#ec4899", // Pink - Luxury
  BUDGET: "#06b6d4", // Cyan - Budget
  SOLO: "#06b6d4", // Cyan - Solo
  GROUP: "#f97316", // Amber - Group
  FAMILY: "#ef4444", // Red - Family
  ROMANTIC: "#9c032eff", // Romantic color
  OTHER: "#6b7280", // Gray - Other
};
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