import { YouTubeComment } from "../entities/youtube_comment.entity";
import {
  YoutubeCommentListWithMeta,
  youtubeCommentRepository,
} from "../repositories/youtube_comment.repository";

export class YouTubeCommentService {
  // Service methods for YouTubeComment entity
  async getYoutubeComments(
    limit: number,
    offset: number,
    timeRange: string
  ): Promise<YoutubeCommentListWithMeta> {
    return youtubeCommentRepository.findAll(
      limit,
      offset,
      timeRange
    );
  }

  async getYoutubeCommentsById(id: string): Promise<YouTubeComment | null> {
    return youtubeCommentRepository.findById(id);
  }

  async getYoutubeCommentsByVideoId(
    videoId: string,
    limit: number,
    offset: number,
    timeRange: string
  ): Promise<YoutubeCommentListWithMeta> {
    return youtubeCommentRepository.findByVideoId(
      videoId,
      limit,
      offset,
      timeRange
    );
  }

  async getYoutubeCommentsIntentionsByVideoId(
    videoId: string,
    limit: number,
    offset: number,
    intention_type: string,

    timeRange: string
  ): Promise<YoutubeCommentListWithMeta> {
    return youtubeCommentRepository.findIntentionByVideoId(
      videoId,
      limit,
      offset,
      intention_type,
      timeRange
    );
  }
  async getYoutubeCommentsTravelingTypeByVideoId(
    videoId: string,
    limit: number,
    offset: number,
    traveling_type: string,
    timeRange: string
  ): Promise<YoutubeCommentListWithMeta> {
    return youtubeCommentRepository.findTravelingTypeByVideoId(
      videoId,
      limit,
      offset,
      traveling_type,
      timeRange
    );
  }
}

export const youtubeCommentService = new YouTubeCommentService();
