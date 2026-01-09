import { Router } from "express";
import { youtubeCommentService } from "../services/youtube_comment.service";

export const youtubeCommentRouter = Router();

youtubeCommentRouter.get("/", async (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    const timeRange = (req.query.timeRange as string) || "all";
    const intention_type = (req.query.intention_type as string) || "all";
    const traveling_type = (req.query.traveling_type as string) || "all";

    const data = await youtubeCommentService.getYoutubeComments(
      limit,
      offset,
      timeRange
    );
    res.json({ success: true, data });
  } catch (error) {
    console.error("Error fetching YouTube comments:", error);
    res
      .status(500)
      .json({ success: false, error: "Failed to fetch YouTube comments" });
  }
});

youtubeCommentRouter.get("/:id", async (req, res) => {
  try {
    const data = await youtubeCommentService.getYoutubeCommentsById(
      req.params.id
    );
    res.json({ success: true, data });
  } catch (error) {
    console.error("Error fetching YouTube comment by ID:", error);
    res
      .status(500)
      .json({ success: false, error: "Failed to fetch YouTube comment by ID" });
  }
});

youtubeCommentRouter.get("/video/:videoId", async (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    const timeRange = (req.query.timeRange as string) || "all";
    const intention_type = (req.query.intention_type as string) || "all";
    const traveling_type = (req.query.traveling_type as string) || "all";

    const id = req.params.videoId;

    const data = await youtubeCommentService.getYoutubeCommentsByVideoId(
      id,
      limit,
      offset,
      timeRange
    );
    res.json({ success: true, data });
  } catch (error) {
    console.error("Error fetching YouTube comments by video ID:", error);
    res.status(500).json({
      success: false,
      error: "Failed to fetch YouTube comments by video ID",
    });
  }
});


youtubeCommentRouter.get("/video/:videoId/intention", async (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    const timeRange = (req.query.timeRange as string) || "all";
    const intention_type = (req.query.intention_type as string) || "all";
    

    const id = req.params.videoId;

    const data = await youtubeCommentService.getYoutubeCommentsIntentionsByVideoId(
      id,
      limit,
      offset,
      intention_type,
      timeRange
    );
    res.json({ success: true, data });
  } catch (error) {
    console.error("Error fetching YouTube comments intention by video ID:", error);
    res.status(500).json({
      success: false,
      error: "Failed to fetch YouTube comments intention by video ID",
    });
  }
});

youtubeCommentRouter.get("/video/:videoId/traveling_type", async (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    const timeRange = (req.query.timeRange as string) || "all";
    const traveling_type = (req.query.traveling_type as string) || "all";

    const id = req.params.videoId;

    const data = await youtubeCommentService.getYoutubeCommentsTravelingTypeByVideoId(
      id,
      limit,
      offset,
      traveling_type,
      timeRange
    );
    res.json({ success: true, data });
  } catch (error) {
    console.error("Error fetching YouTube comments traveling type by video ID:", error);
    res.status(500).json({
      success: false,
      error: "Failed to fetch YouTube comments traveling type by video ID",
    });
  }
});