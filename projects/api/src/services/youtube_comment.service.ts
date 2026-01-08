import { YouTubeComment } from "../entities/youtube_comment.entity";
import { youtubeCommentRepository } from "../repositories/youtube_comment.repository";

export class YouTubeCommentService {
  // Service methods for YouTubeComment entity
  async getYoutubeComments(): Promise<YouTubeComment[]> {
    return youtubeCommentRepository.findAll();
  }

  async getYoutubeCommentsById(id: string): Promise<YouTubeComment | null> {
    return youtubeCommentRepository.findById(id);
  }

  async getYoutubeCommentsByVideoId(
    videoId: string
  ): Promise<YouTubeComment[]> {
    return youtubeCommentRepository.findByVideoId(videoId);
  }
}

export const youtubeCommentService = new YouTubeCommentService();