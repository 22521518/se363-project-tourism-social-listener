/**
 * ASCA (Aspect-based Sentiment Category Analysis) types for the frontend.
 * Maps to backend DTOs from projects/services/processing/tasks/asca
 */

// Aspect categories matching ASCA labels
export type CategoryType = 'LOCATION' | 'PRICE' | 'ACCOMMODATION' | 'FOOD' | 'SERVICE' | 'AMBIENCE';

// Sentiment types
export type SentimentType = 'positive' | 'negative' | 'neutral';

// Extractor type
export type ExtractorType = 'asca' | 'manual';

/**
 * A single aspect-sentiment pair extracted from text.
 */
export interface AspectSentiment {
  category: CategoryType;
  sentiment: SentimentType;
  confidence: number;
}

/**
 * Metadata about the extraction process.
 */
export interface ExtractionMeta {
  extractor: ExtractorType;
  language: string;
  model_version?: string;
}

/**
 * Complete ASCA extraction result for a single source.
 */
export interface ASCAExtraction {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  aspects: AspectSentiment[];
  overall_score: number;
  meta?: ExtractionMeta;
  is_approved: boolean;
  approved_result?: Record<string, unknown>;
  is_deleted: boolean;
  created_at: string;
}

/**
 * Statistics for ASCA analysis display.
 */
export interface ASCAStats {
  category: CategoryType;
  positive: number;
  negative: number;
  neutral: number;
  total: number;
}

/**
 * Aggregated ASCA data with metadata.
 */
export interface ASCAStatsResponse {
  total_processed: number;
  approved_count: number;
  pending_count: number;
  by_category: ASCAStats[];
  period_start?: string;
  period_end?: string;
}

// Colors for categories
export const CATEGORY_COLORS: Record<CategoryType, string> = {
  LOCATION: '#3b82f6',      // Blue
  PRICE: '#10b981',         // Green
  ACCOMMODATION: '#8b5cf6', // Purple
  FOOD: '#f59e0b',          // Amber
  SERVICE: '#ec4899',       // Pink
  AMBIENCE: '#06b6d4',      // Cyan
};

// Colors for sentiments
export const SENTIMENT_COLORS: Record<SentimentType, string> = {
  positive: '#22c55e',  // Green
  negative: '#ef4444',  // Red
  neutral: '#6b7280',   // Gray
};
