import { Router, Request, Response } from "express";
import { travelingTypeService } from "../services/traveling_type.service";

export const travelingTypeRouter = Router();

travelingTypeRouter.get("/stats", async (_req: Request, res: Response) => {
  try {
    const stats = await travelingTypeService.getTravelingTypeStats();
    res.json({ success: true, data: stats });
  } catch (error) {
    console.error("Error fetching traveling type stats:", error);
    res
      .status(500)
      .json({ success: false, error: "Failed to fetch traveling type stats" });
  }
});

travelingTypeRouter.get(
  "/stats/video/:id",
  async (_req: Request, res: Response) => {
    try {
      const id = _req.params.id;
      const stats = await travelingTypeService.getVideoTravelingTypeStats(id);
      res.json({ success: true, data: stats });
    } catch (error) {
      console.error("Error fetching traveling type stats:", error);
      res.status(500).json({
        success: false,
        error: "Failed to fetch traveling type stats",
      });
    }
  }
);

travelingTypeRouter.get(
  "/video/:id/raw",
  async (_req: Request, res: Response) => {
    try {
      const id = _req.params.id;
      const travelingTypes = await travelingTypeService.getVideoTravelingTypes(id);
      res.json({ success: true, data: travelingTypes });
    } catch (error) {
      console.error("Error fetching video traveling types:", error);
      res.status(500).json({
        success: false,
        error: "Failed to fetch video traveling types",
      });
    }
  }
);
