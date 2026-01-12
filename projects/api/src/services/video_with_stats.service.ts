import {
  videoWithStatsRepository,
  VideoWithStatsListResponse,
} from "../repositories/video_with_stats.repository";
import { YouTubeCommentWithStats } from "../entities/video_with_stats.entity";

export interface CommentsWithStatsResponse {
  data: YouTubeCommentWithStats[];
  meta: {
    total: number;
    hasMore: boolean;
  };
}

export class VideoWithStatsService {
  /**
   * Get videos with full processing stats
   */
  async getVideosWithStats(
    limit: number,
    offset: number,
    channel: string,
    timeRange: string,
    filters?: {
      sentiment?: string;
      intention?: string;
      travelType?: string;
      aspect?: string;
    }
  ): Promise<VideoWithStatsListResponse> {
    return videoWithStatsRepository.findAllWithStats(
      limit,
      offset,
      channel,
      timeRange,
      filters
    );
  }

  /**
   * Get comments for a video with processing results
   */
  async getCommentsWithStats(
    videoId: string,
    limit: number,
    offset: number
  ): Promise<CommentsWithStatsResponse> {
    return videoWithStatsRepository.getCommentsWithStats(videoId, limit, offset);
  }
}

export const videoWithStatsService = new VideoWithStatsService();
