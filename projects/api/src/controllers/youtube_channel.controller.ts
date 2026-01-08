import { Router } from "express";
import { youtubeChannelService } from "../services/youtube_channel.service";

export const youtubeChannelRouter = Router();

youtubeChannelRouter.get("/", async (req, res) => {
  try {
    const data = await youtubeChannelService.getYoutubeChannels();
    res.json({ success: true, data });
  } catch (error) {
    console.error("Error fetching YouTube channels:", error);
    res
      .status(500)
      .json({ success: false, error: "Failed to fetch YouTube channels" });
  }
});
