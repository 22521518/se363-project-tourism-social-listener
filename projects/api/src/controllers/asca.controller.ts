import { Router, Request, Response } from "express";
import { ascaService } from "../services/asca.service";

export const ascaRouter = Router();

/**
 * @openapi
 * /api/asca/stats:
 *   get:
 *     summary: Get ASCA category statistics
 *     description: Returns aggregated sentiment counts by aspect category
 *     tags:
 *       - ASCA
 *     responses:
 *       200:
 *         description: Successfully retrieved ASCA stats
 */
ascaRouter.get("/stats", async (_req: Request, res: Response) => {
  try {
    const stats = await ascaService.getStats();
    res.json({ success: true, data: stats });
  } catch (error) {
    console.error("Error fetching ASCA stats:", error);
    res.status(500).json({ success: false, error: "Failed to fetch ASCA stats" });
  }
});

/**
 * @openapi
 * /api/asca/stats/video/{id}:
 *   get:
 *     summary: Get ASCA statistics for a specific video
 *     description: Returns aggregated sentiment counts by aspect category for a video's comments
 *     tags:
 *       - ASCA
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: YouTube video ID
 *     responses:
 *       200:
 *         description: Successfully retrieved video ASCA stats
 */
ascaRouter.get("/stats/video/:id", async (req: Request, res: Response) => {
  const { id } = req.params;
  try {
    const stats = await ascaService.getStatsByVideoId(id);
    res.json({ success: true, data: stats });
  } catch (error) {
    console.error("Error fetching video ASCA stats:", error);
    res.status(500).json({ success: false, error: "Failed to fetch video ASCA stats" });
  }
});

/**
 * @openapi
 * /api/asca/counts:
 *   get:
 *     summary: Get ASCA total counts
 *     description: Returns total, approved, and pending counts
 *     tags:
 *       - ASCA
 *     responses:
 *       200:
 *         description: Successfully retrieved counts
 */
ascaRouter.get("/counts", async (_req: Request, res: Response) => {
  try {
    const counts = await ascaService.getTotalCounts();
    res.json({ success: true, data: counts });
  } catch (error) {
    console.error("Error fetching ASCA counts:", error);
    res.status(500).json({ success: false, error: "Failed to fetch ASCA counts" });
  }
});
