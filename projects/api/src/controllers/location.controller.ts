import { Router, Request, Response } from 'express';
import { locationService } from '../services/location.service';

export const locationRouter = Router();

/**
 * @openapi
 * /api/locations/geography:
 *   get:
 *     summary: Get geography statistics by region
 *     description: |
 *       Returns aggregated location counts categorized by geographic region relative to Vietnam:
 *       - **Domestic**: Locations within Vietnam (cities, provinces, landmarks)
 *       - **Regional**: South East Asia countries (Thailand, Cambodia, Malaysia, Singapore, etc.)
 *       - **International**: Rest of the world
 *     tags:
 *       - Locations
 *     responses:
 *       200:
 *         description: Successfully retrieved geography statistics
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/GeographyStatsResponse'
 *             example:
 *               success: true
 *               data:
 *                 - name: Domestic
 *                   value: 5200
 *                   color: "#3b82f6"
 *                 - name: International
 *                   value: 4800
 *                   color: "#10b981"
 *                 - name: Regional
 *                   value: 3100
 *                   color: "#f59e0b"
 *       500:
 *         description: Server error
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ErrorResponse'
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
