import { Router, Request, Response } from "express";
import { intentionService } from "../services/intention.service";

export const intentionRouter = Router();

intentionRouter.get("/stats", async (_req: Request, res: Response) => {
  try {
    const stats = await intentionService.getIntentionStats();
    res.json({ success: true, data: stats });
  } catch (error) {
    console.error("Error fetching intention stats:", error);
    res
      .status(500)
      .json({ success: false, error: "Failed to fetch intention stats" });
  }
});

intentionRouter.get(
  "/stats/video/:id",
  async (_req: Request, res: Response) => {
    const id = _req.params.id;
    try {
      const stats = await intentionService.getVideoIntentionStats(id);
      res.json({ success: true, data: stats });
    } catch (error) {
      console.error("Error fetching video intention stats:", error);
      res
        .status(500)
        .json({
          success: false,
          error: "Failed to fetch video intention stats",
        });
    }
  }
);
