import { Router, Request, Response } from "express";
import { videoWithStatsService } from "../services/video_with_stats.service";

export const videoWithStatsRouter = Router();

/**
 * @openapi
 * /api/videos_with_stats:
 *   get:
 *     summary: Get videos with aggregated processing stats
 *     description: Returns videos with sentiment, intention, travel type, location, and ASCA stats
 *     tags:
 *       - Videos With Stats
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
 *         name: channel
 *         schema:
 *           type: string
 *           default: all
 *       - in: query
 *         name: time_range
 *         schema:
 *           type: string
 *           enum: [all, 24h, 7d, 30d, 90d, 6m, 1y]
 *     responses:
 *       200:
 *         description: Successfully retrieved videos with stats
 */
videoWithStatsRouter.get("/", async (req: Request, res: Response) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    const channel = (req.query.channel as string) || "all";
    const timeRange = (req.query.time_range as string) || "all";
    const filters = {
      sentiment: req.query.sentiment as string | undefined,
      intention: req.query.intention as string | undefined,
      travelType: req.query.travel_type as string | undefined,
      aspect: req.query.aspect as string | undefined,
    };

    const result = await videoWithStatsService.getVideosWithStats(
      limit,
      offset,
      channel,
      timeRange,
      filters
    );

    res.json({ success: true, ...result });
  } catch (error) {
    console.error("Error fetching videos with stats:", error);
    res.status(500).json({ success: false, error: "Failed to fetch videos with stats" });
  }
});

/**
 * @openapi
 * /api/videos_with_stats/{videoId}/comments:
 *   get:
 *     summary: Get comments for a video with processing results
 *     description: Returns comments with sentiment, intention, travel type, and locations
 *     tags:
 *       - Videos With Stats
 *     parameters:
 *       - in: path
 *         name: videoId
 *         required: true
 *         schema:
 *           type: string
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
 *     responses:
 *       200:
 *         description: Successfully retrieved comments with stats
 */
videoWithStatsRouter.get("/:videoId/comments", async (req: Request, res: Response) => {
  try {
    const { videoId } = req.params;
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;

    const result = await videoWithStatsService.getCommentsWithStats(videoId, limit, offset);

    res.json({ success: true, ...result });
  } catch (error) {
    console.error("Error fetching comments with stats:", error);
    res.status(500).json({ success: false, error: "Failed to fetch comments with stats" });
  }
});
