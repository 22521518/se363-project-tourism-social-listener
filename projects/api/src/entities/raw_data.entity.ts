/**
 * Raw Data Entity Types
 * Represents source data (YouTube comments, WebCrawl) with processing status
 */

export type SourceType = 'youtube_comment' | 'webcrawl';

export type ProcessingTask = 'asca' | 'intention' | 'location_extraction' | 'traveling_type';

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
  published_at: Date;
}

export interface WebCrawlMetadata {
  url: string;
  title: string | null;
  content_type: string;
  crawl_time: Date;
}

export interface RawDataItem {
  id: string;
  source_type: SourceType;
  text: string;
  metadata: YouTubeCommentMetadata | WebCrawlMetadata;
  processing_status: ProcessingStatus;
  created_at: Date;
}

export interface RawDataListResponse {
  data: RawDataItem[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
  summary: {
    total_items: number;
    processed_counts: {
      asca: number;
      intention: number;
      location_extraction: number;
      traveling_type: number;
    };
  };
}

export type ProcessingFilter = 'all' | 'processed' | 'unprocessed';
