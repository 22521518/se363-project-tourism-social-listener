import { rawDataRepository } from '../repositories/raw_data.repository';
import {
  RawDataListResponse,
  ProcessingTask,
  ProcessingFilter,
  SourceType,
} from '../entities/raw_data.entity';

export class RawDataService {
  /**
   * Get raw data items with processing status
   */
  async getRawData(
    sourceType: SourceType | 'all',
    limit: number,
    offset: number,
    processingFilter: ProcessingFilter = 'all',
    task: ProcessingTask | 'all' = 'all'
  ): Promise<RawDataListResponse> {
    if (sourceType === 'youtube_comment') {
      return rawDataRepository.findYouTubeComments(limit, offset, processingFilter, task);
    } else if (sourceType === 'webcrawl') {
      return rawDataRepository.findWebCrawlData(limit, offset, processingFilter, task);
    } else {
      // Combine both sources - get YouTube comments by default
      return rawDataRepository.findYouTubeComments(limit, offset, processingFilter, task);
    }
  }

  /**
   * Get YouTube comments with processing status
   */
  async getYouTubeComments(
    limit: number,
    offset: number,
    processingFilter: ProcessingFilter = 'all',
    task: ProcessingTask | 'all' = 'all'
  ): Promise<RawDataListResponse> {
    return rawDataRepository.findYouTubeComments(limit, offset, processingFilter, task);
  }

  /**
   * Get WebCrawl data with processing status
   */
  async getWebCrawlData(
    limit: number,
    offset: number,
    processingFilter: ProcessingFilter = 'all',
    task: ProcessingTask | 'all' = 'all'
  ): Promise<RawDataListResponse> {
    return rawDataRepository.findWebCrawlData(limit, offset, processingFilter, task);
  }

  /**
   * Get processing details for a specific source item
   */
  async getProcessingDetails(sourceId: string) {
    return rawDataRepository.getProcessingDetails(sourceId);
  }
}

export const rawDataService = new RawDataService();
