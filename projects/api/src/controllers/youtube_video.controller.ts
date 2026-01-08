import { Router } from "express";
import { youtubeVideoService } from "../services/youtube_video.service";

export const youtubeVideoRouter = Router();

youtubeVideoRouter.get("/", async (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    const data = await youtubeVideoService.getYoutubeVideos(limit, offset);
    res.json({ success: true, data });
  } catch (error) {
    console.error("Error fetching YouTube videos:", error);
    res
      .status(500)
      .json({ success: false, error: "Failed to fetch YouTube videos" });
  }
});

youtubeVideoRouter.get("/:id", async (req, res) => {
  try {
    const data = await youtubeVideoService.getYoutubeVideosById(req.params.id);
    res.json({ success: true, data });
  } catch (error) {
    console.error("Error fetching YouTube video by ID:", error);
    res
      .status(500)
      .json({ success: false, error: "Failed to fetch YouTube video by ID" });
  }
});
