import { Router } from "express";
import { youtubeCommentService } from "../services/youtube_comment.service";

export const youtubeCommentRouter = Router();

youtubeCommentRouter.get("/", async (req, res) => {
  try {
    const data = await youtubeCommentService.getYoutubeComments();
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
    const data = await youtubeCommentService.getYoutubeCommentsByVideoId(
      req.params.videoId
    );
    res.json({ success: true, data });
  } catch (error) {
    console.error("Error fetching YouTube comments by video ID:", error);
    res
      .status(500)
      .json({
        success: false,
        error: "Failed to fetch YouTube comments by video ID",
      });
  }
});
