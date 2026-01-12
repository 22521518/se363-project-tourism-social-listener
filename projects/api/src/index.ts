import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import swaggerUi from 'swagger-ui-express';
import { locationRouter } from './controllers/location.controller';
import { swaggerSpec } from './config/swagger';
import { intentionRouter } from './controllers/intention.controller';
import { travelingTypeRouter } from './controllers/traveling_type.controller';
import { youtubeChannelRouter } from './controllers/youtube_channel.controller';
import { youtubeVideoRouter } from './controllers/youtube_video.controller';
import { youtubeCommentRouter } from './controllers/youtube_comment.controller';
import { ascaRouter } from './controllers/asca.controller';
import { crawlRouter } from './controllers/crawl.controller';
import { videoWithStatsRouter } from './controllers/video_with_stats.controller';
import { rawDataRouter } from './controllers/raw_data.controller';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Swagger Documentation
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Routes
app.use('/api/locations', locationRouter);
app.use('/api/intentions', intentionRouter);
app.use('/api/traveling_types', travelingTypeRouter);
app.use('/api/youtube_channels', youtubeChannelRouter);
app.use('/api/youtube_videos', youtubeVideoRouter);
app.use('/api/youtube_comments', youtubeCommentRouter);
app.use('/api/asca', ascaRouter);
app.use('/api/crawl_results', crawlRouter);
app.use('/api/videos_with_stats', videoWithStatsRouter);
app.use('/api/raw_data', rawDataRouter);

// Health check
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`🚀 API server running on http://localhost:${PORT}`);
  console.log(`📚 Swagger docs at http://localhost:${PORT}/api-docs`);
});
