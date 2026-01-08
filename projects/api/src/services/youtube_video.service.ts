import { YouTubeVideo } from "../entities/youtube_video.entity";
import { youtubeVideoRepository } from "../repositories/youtube_video.repository";

export class YouTubeVideoService {
  // Service methods for YouTubeVideo entity
  async getYoutubeVideos(limit: number, offset: number): Promise<YouTubeVideo[]> {
    // Implementation to retrieve YouTube videos
    return youtubeVideoRepository.findAll(limit, offset);
  }

  async getYoutubeVideosById(id: string): Promise<YouTubeVideo | null> {
    // Implementation to retrieve a YouTube video by ID
    return youtubeVideoRepository.findById(id);
  }

}

export const youtubeVideoService = new YouTubeVideoService();