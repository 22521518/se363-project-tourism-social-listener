import { Router, Request, Response } from 'express';
import { locationService } from '../services/location.service';

export const locationRouter = Router();

/**
 * GET /api/locations/geography
 * Returns aggregated location counts by type for "By Geography" chart.
 */
locationRouter.get('/geography', async (_req: Request, res: Response) => {
  try {
    const stats = await locationService.getGeographyStats();
    res.json({ success: true, data: stats });
  } catch (error) {
    console.error('Error fetching geography stats:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch geography stats' });
  }
});
