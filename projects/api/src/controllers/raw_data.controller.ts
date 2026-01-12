import { Router, Request, Response } from 'express';
import { rawDataService } from '../services/raw_data.service';
import { ProcessingFilter, ProcessingTask } from '../entities/raw_data.entity';

export const rawDataRouter = Router();

/**
 * @openapi
 * /api/raw_data/youtube:
 *   get:
 *     summary: Get YouTube comments with processing status
 *     description: Returns YouTube comments with processing status for each task (asca, intention, location, traveling_type)
 *     tags:
 *       - Raw Data
 *     parameters:
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 20
 *       - in: query
 *         name: offset
 *         schema:
 *           type: integer
 *           default: 0
 *       - in: query
 *         name: processing_status
 *         schema:
 *           type: string
 *           enum: [all, processed, unprocessed]
 *           default: all
 *       - in: query
 *         name: task
 *         schema:
 *           type: string
 *           enum: [all, asca, intention, location_extraction, traveling_type]
 *           default: all
 *     responses:
 *       200:
 *         description: Successfully retrieved YouTube comments with processing status
 */
rawDataRouter.get('/youtube', async (req: Request, res: Response) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    const processingFilter = (req.query.processing_status as ProcessingFilter) || 'all';
    const task = (req.query.task as ProcessingTask | 'all') || 'all';

    const result = await rawDataService.getYouTubeComments(
      limit,
      offset,
      processingFilter,
      task
    );

    res.json({ success: true, ...result });
  } catch (error) {
    console.error('Error fetching YouTube comments with processing status:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch YouTube comments' });
  }
});

/**
 * @openapi
 * /api/raw_data/webcrawl:
 *   get:
 *     summary: Get WebCrawl data with processing status
 *     description: Returns WebCrawl data with processing status for each task
 *     tags:
 *       - Raw Data
 *     parameters:
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 20
 *       - in: query
 *         name: offset
 *         schema:
 *           type: integer
 *           default: 0
 *       - in: query
 *         name: processing_status
 *         schema:
 *           type: string
 *           enum: [all, processed, unprocessed]
 *           default: all
 *       - in: query
 *         name: task
 *         schema:
 *           type: string
 *           enum: [all, asca, intention, location_extraction, traveling_type]
 *           default: all
 *     responses:
 *       200:
 *         description: Successfully retrieved WebCrawl data with processing status
 */
rawDataRouter.get('/webcrawl', async (req: Request, res: Response) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    const processingFilter = (req.query.processing_status as ProcessingFilter) || 'all';
    const task = (req.query.task as ProcessingTask | 'all') || 'all';

    console.log('WebCrawl request params:', { limit, offset, processingFilter, task });

    const result = await rawDataService.getWebCrawlData(
      limit,
      offset,
      processingFilter,
      task
    );

    res.json({ success: true, ...result });
  } catch (error) {
    console.error('Error fetching WebCrawl data with processing status:', error);
    console.error('Stack trace:', error instanceof Error ? error.stack : 'No stack');
    res.status(500).json({ success: false, error: 'Failed to fetch WebCrawl data' });
  }
});

/**
 * @openapi
 * /api/raw_data/{sourceId}/processing:
 *   get:
 *     summary: Get processing details for a specific source item
 *     description: Returns detailed processing results from all tasks (ASCA, Intention, Location, Traveling Type)
 *     tags:
 *       - Raw Data
 *     parameters:
 *       - in: path
 *         name: sourceId
 *         required: true
 *         schema:
 *           type: string
 *         description: The source item ID (comment ID or webcrawl request ID)
 *     responses:
 *       200:
 *         description: Successfully retrieved processing details
 */
rawDataRouter.get('/:sourceId/processing', async (req: Request, res: Response) => {
  try {
    const { sourceId } = req.params;

    if (!sourceId) {
      res.status(400).json({ success: false, error: 'sourceId is required' });
      return;
    }

    const result = await rawDataService.getProcessingDetails(sourceId);
    res.json({ success: true, data: result });
  } catch (error) {
    console.error('Error fetching processing details:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch processing details' });
  }
});
