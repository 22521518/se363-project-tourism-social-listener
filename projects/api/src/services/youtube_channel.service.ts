import { YouTubeChannel } from "../entities/youtube_channel.entity";
import { youTubeChannelRepository } from "../repositories/youtube_channel.repository";

export class YouTubeChannelService {
    // Service methods for YouTubeChannel entity
    async getYoutubeChannels(): Promise<YouTubeChannel[]> {
        return await youTubeChannelRepository.findAll();
    }
}

export const youtubeChannelService = new YouTubeChannelService();