/**
 * ASCA Extraction Entity
 * Represents aspect-based sentiment analysis results
 */

export type CategoryType = 'LOCATION' | 'PRICE' | 'ACCOMMODATION' | 'FOOD' | 'SERVICE' | 'AMBIENCE';
export type SentimentType = 'positive' | 'negative' | 'neutral';

export interface AspectSentiment {
  category: CategoryType;
  sentiment: SentimentType;
  confidence: number;
}

export interface ASCAExtraction {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  aspects: AspectSentiment[];
  overall_score: number;
  meta: Record<string, unknown>;
  is_approved: boolean;
  approved_result: Record<string, unknown> | null;
  is_deleted: boolean;
  created_at: Date;
  updated_at: Date;
}

export interface ASCACategoryStats {
  category: CategoryType;
  positive: number;
  negative: number;
  neutral: number;
  total: number;
}

export interface ASCAStatsResponse {
  total_processed: number;
  approved_count: number;
  pending_count: number;
  by_category: ASCACategoryStats[];
}
