// YouTube Ingestion - TypeScript Type Definitions
// Shared contracts for YouTube entities

/**
 * YouTube Channel metadata
 */
export interface YouTubeChannel {
  id: string;
  title: string;
  description: string;
  customUrl?: string;
  publishedAt: string; // ISO datetime
  thumbnailUrl: string;
  subscriberCount: number;
  videoCount: number;
  viewCount: number;
  country?: string;
}

/**
 * YouTube Video metadata
 */
export interface YouTubeVideo {
  id: string;
  channelId: string;
  title: string;
  description: string;
  publishedAt: string; // ISO datetime
  thumbnailUrl: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  duration: string; // ISO 8601 duration
  tags: string[];
  categoryId?: string;
}

/**
 * YouTube Comment
 */
export interface YouTubeComment {
  id: string;
  videoId: string;
  authorDisplayName: string;
  authorChannelId?: string;
  text: string;
  likeCount: number;
  publishedAt: string; // ISO datetime
  updatedAt: string; // ISO datetime
  parentId?: string; // For replies
  replyCount: number;
}

/**
 * Raw ingestion message format
 * Standard output format for all ingestion connectors
 */
export interface RawIngestionMessage {
  source: 'youtube' | string;
  externalId: string;
  rawText: string;
  createdAt: string; // ISO datetime
  rawPayload: Record<string, unknown>;
  entityType: 'channel' | 'video' | 'comment';
}

/**
 * Tracked channel state
 */
export interface TrackedChannel {
  channelId: string;
  lastChecked: string; // ISO datetime
  lastVideoPublished?: string; // ISO datetime
  isActive: boolean;
}

/**
 * Kafka event wrapper
 */
export interface YouTubeEvent<T = YouTubeChannel | YouTubeVideo | YouTubeComment> {
  topic: string;
  key: string;
  value: RawIngestionMessage;
  timestamp: string;
  entity: T;
}

/**
 * Ingestion job status
 */
export interface IngestionJob {
  id: string;
  channelId: string;
  jobType: 'full' | 'videos' | 'comments';
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: string;
  completedAt?: string;
  error?: string;
  result?: {
    videosCount?: number;
    commentsCount?: number;
  };
}
