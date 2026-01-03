import { Router, Request, Response } from 'express';
import { travelingTypeService } from '../services/traveling_type.service';

export const travelingTypeRouter = Router();

/**
 * @openapi
 * /api/traveling_types/stats:
 *   get:
 *     summary: Get traveling type statistics
 *     description: |
 *       Returns aggregated traveling type counts categorized by type:
 *       - **Business**: Business travel
 *       - **Leisure**: Leisure travel
 *       - **Adventure**: Adventure travel
 *       - **Backpacking**: Backpacking travel
 *       - **Luxury**: Luxury travel
 *       - **Budget**: Budget travel
 *       - **Solo**: Solo travel
 *       - **Group**: Group travel
 *       - **Family**: Family travel
 *       - **Romantic**: Romantic travel
 *       - **Other**: Other types of travel
 *     tags:
 *       - Traveling Types
 *     responses:
 *       200:
 *         description: Successfully retrieved traveling type statistics
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/TravelingTypeStatsResponse'
 *             example:
 *               success: true
 *               data:
 *                  - name: Business
 *                    value: 5200
 *                    color: "#3b82f6"
 *                  - name: Leisure
 *                    value: 4800
 *                    color: "#10b981"
 *                  - name: Adventure
 *                    value: 3100
 *                    color: "#f59e0b"
 *                  - name: Backpacking
 *                    value: 2800
 *                    color: "#8b5cf6"
 *                  - name: Luxury
 *                    value: 2400
 *                    color: "#ec4899"
 *                  - name: Budget
 *                    value: 3600
 *                    color: "#06b6d4"
 *                  - name: Solo
 *                    value: 2100
 *                    color: "#06b6d4"
 *                  - name: Group
 *                    value: 3900
 *                    color: "#f97316"
 *                  - name: Family
 *                    value: 4200
 *                    color: "#ef4444"
 *                  - name: Romantic
 *                    value: 2600
 *                    color: "#9c032e"
 *                  - name: Other
 *                    value: 1500
 *                    color: "#6b7280"
 *       500:
 *         description: Server error
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ErrorResponse'
 */
travelingTypeRouter.get('/stats', async (_req: Request, res: Response) => {
  try {
    const stats = await travelingTypeService.getTravelingTypeStats();
    res.json({ success: true, data: stats });
  } catch (error) {
    console.error('Error fetching traveling type stats:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch traveling type stats' });
  }
});
