/**
 * Raw Data Types with Processing Status
 * For displaying YouTube comments and WebCrawl data with task processing indicators
 */

export type SourceType = 'youtube_comment' | 'webcrawl';

export type ProcessingTask = 'asca' | 'intention' | 'location_extraction' | 'traveling_type';

export type ProcessingFilter = 'all' | 'processed' | 'unprocessed';

export interface ProcessingStatus {
  asca: boolean;
  intention: boolean;
  location_extraction: boolean;
  traveling_type: boolean;
}

export interface YouTubeCommentMetadata {
  video_id: string;
  video_title?: string;
  channel_title?: string;
  author_name: string | null;
  like_count: number;
  published_at: string;
}

export interface WebCrawlMetadata {
  url: string;
  title: string | null;
  content_type: string;
  crawl_time: string;
}

export interface RawDataItem {
  id: string;
  source_type: SourceType;
  text: string;
  metadata: YouTubeCommentMetadata | WebCrawlMetadata;
  processing_status: ProcessingStatus;
  created_at: string;
}

export interface ProcessingSummary {
  total_items: number;
  processed_counts: {
    asca: number;
    intention: number;
    location_extraction: number;
    traveling_type: number;
  };
}

export interface RawDataResponse {
  success: boolean;
  data: RawDataItem[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
  summary: ProcessingSummary;
}

// Task Label Mapping
export const TASK_LABELS: Record<ProcessingTask, string> = {
  asca: 'ASCA Analysis',
  intention: 'Intention',
  location_extraction: 'Location',
  traveling_type: 'Traveling Type',
};

export const TASK_COLORS: Record<ProcessingTask, string> = {
  asca: '#8b5cf6',
  intention: '#3b82f6',
  location_extraction: '#10b981',
  traveling_type: '#f59e0b',
};
