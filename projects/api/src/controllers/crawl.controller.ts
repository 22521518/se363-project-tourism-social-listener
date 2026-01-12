import { Router, Request, Response } from "express";
import { crawlService } from "../services/crawl.service";

export const crawlRouter = Router();

/**
 * @openapi
 * /api/crawl_results:
 *   get:
 *     summary: Get paginated web crawl results
 *     description: Returns crawled web content including reviews, comments, and blog sections
 *     tags:
 *       - Web Crawl
 *     parameters:
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 20
 *         description: Number of results to return
 *       - in: query
 *         name: offset
 *         schema:
 *           type: integer
 *           default: 0
 *         description: Offset for pagination
 *       - in: query
 *         name: content_type
 *         schema:
 *           type: string
 *           enum: [forum, review, blog, agency, auto, all]
 *         description: Filter by content type
 *     responses:
 *       200:
 *         description: Successfully retrieved crawl results
 */
crawlRouter.get("/", async (req: Request, res: Response) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    const contentType = req.query.content_type as string | undefined;

    const results = await crawlService.getResults(limit, offset, contentType);
    res.json({ success: true, ...results });
  } catch (error) {
    console.error("Error fetching crawl results:", error);
    res.status(500).json({ success: false, error: "Failed to fetch crawl results" });
  }
});

/**
 * @openapi
 * /api/crawl_results/stats:
 *   get:
 *     summary: Get web crawl statistics
 *     description: Returns aggregated stats by content type
 *     tags:
 *       - Web Crawl
 *     responses:
 *       200:
 *         description: Successfully retrieved crawl stats
 */
crawlRouter.get("/stats", async (_req: Request, res: Response) => {
  try {
    const stats = await crawlService.getStats();
    res.json({ success: true, data: stats });
  } catch (error) {
    console.error("Error fetching crawl stats:", error);
    res.status(500).json({ success: false, error: "Failed to fetch crawl stats" });
  }
});
