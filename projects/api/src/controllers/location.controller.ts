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

/**
 * @openapi
 * /api/locations/continents:
 *   get:
 *     summary: Get location statistics by continent
 *     tags:
 *       - Locations
 *     responses:
 *       200:
 *         description: Successfully retrieved continent statistics
 */
locationRouter.get('/continents', async (_req: Request, res: Response) => {
  try {
    const result = await locationService.getContinentStats();
    res.json({ success: true, ...result });
  } catch (error) {
    console.error('Error fetching continent stats:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch continent stats' });
  }
});

/**
 * @openapi
 * /api/locations/countries:
 *   get:
 *     summary: Get countries for a specific continent
 *     tags:
 *       - Locations
 *     parameters:
 *       - in: query
 *         name: continent
 *         required: true
 *         schema:
 *           type: string
 *         description: Continent ID (asia, europe, north_america, south_america, africa, oceania)
 *     responses:
 *       200:
 *         description: Successfully retrieved country statistics
 */
locationRouter.get('/countries', async (req: Request, res: Response) => {
  try {
    const continent = (req.query.continent as string) || '';
    if (!continent) {
      res.status(400).json({ success: false, error: 'continent parameter is required' });
      return;
    }
    const result = await locationService.getCountriesForContinent(continent);
    res.json({ success: true, ...result });
  } catch (error) {
    console.error('Error fetching country stats:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch country stats' });
  }
});

/**
 * @openapi
 * /api/locations/regions:
 *   get:
 *     summary: Get regions for a specific country
 *     tags:
 *       - Locations
 *     parameters:
 *       - in: query
 *         name: country
 *         required: true
 *         schema:
 *           type: string
 *         description: Country ID
 *     responses:
 *       200:
 *         description: Successfully retrieved region statistics
 */
locationRouter.get('/regions', async (req: Request, res: Response) => {
  try {
    const country = (req.query.country as string) || '';
    if (!country) {
      res.status(400).json({ success: false, error: 'country parameter is required' });
      return;
    }
    const result = await locationService.getRegionsForCountry(country);
    res.json({ success: true, ...result });
  } catch (error) {
    console.error('Error fetching region stats:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch region stats' });
  }
});
