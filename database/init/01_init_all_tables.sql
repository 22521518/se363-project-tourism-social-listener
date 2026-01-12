-- ====================================================================
-- Tourism Social Listener - Database Initialization Script
-- Auto-generated consolidated schema for all services
-- ====================================================================

-- Create extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ====================================================================
-- ENUM TYPES
-- ====================================================================

-- Crawl Status Enum
DO $$ BEGIN
    CREATE TYPE crawl_status AS ENUM ('pending', 'in_progress', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Intention Type Enum
DO $$ BEGIN
    CREATE TYPE intention_type AS ENUM (
        'question', 'feedback', 'complaint', 'suggestion', 
        'praise', 'request', 'discussion', 'spam', 'other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Traveling Type Enum
DO $$ BEGIN
    CREATE TYPE traveling_type AS ENUM (
        'business', 'leisure', 'adventure', 'backpacking',
        'luxury', 'budget', 'solo', 'group', 'family', 'romantic', 'other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ====================================================================
-- YOUTUBE INGESTION TABLES
-- ====================================================================

-- YouTube Channels
CREATE TABLE IF NOT EXISTS youtube_channels (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    custom_url VARCHAR(255),
    published_at TIMESTAMP NOT NULL,
    thumbnail_url VARCHAR(500),
    subscriber_count BIGINT DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    view_count BIGINT DEFAULT 0,
    country VARCHAR(10),
    is_tracked BOOLEAN DEFAULT FALSE,
    last_checked TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_payload JSONB
);

-- YouTube Videos
CREATE TABLE IF NOT EXISTS youtube_videos (
    id VARCHAR(50) PRIMARY KEY,
    channel_id VARCHAR(50) NOT NULL REFERENCES youtube_channels(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    published_at TIMESTAMP NOT NULL,
    thumbnail_url VARCHAR(500),
    view_count BIGINT DEFAULT 0,
    like_count BIGINT DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    duration VARCHAR(50),
    tags TEXT[],
    category_id VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_payload JSONB
);

-- YouTube Comments
CREATE TABLE IF NOT EXISTS youtube_comments (
    id VARCHAR(100) PRIMARY KEY,
    video_id VARCHAR(50) NOT NULL REFERENCES youtube_videos(id) ON DELETE CASCADE,
    author_display_name VARCHAR(255) NOT NULL,
    author_channel_id VARCHAR(50),
    text TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    published_at TIMESTAMP NOT NULL,
    updated_at_youtube TIMESTAMP NOT NULL,
    parent_id VARCHAR(100),
    reply_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_payload JSONB
);

-- YouTube Tracked Channels
CREATE TABLE IF NOT EXISTS youtube_tracked_channels (
    channel_id VARCHAR(50) PRIMARY KEY REFERENCES youtube_channels(id) ON DELETE CASCADE,
    last_checked TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_video_published TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- YouTube Ingestion Checkpoints
CREATE TABLE IF NOT EXISTS youtube_ingestion_checkpoints (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(50) NOT NULL REFERENCES youtube_channels(id) ON DELETE CASCADE,
    operation_type VARCHAR(50) NOT NULL,
    next_page_token VARCHAR(255),
    last_video_id VARCHAR(50),
    fetched_count INTEGER DEFAULT 0,
    target_count INTEGER,
    status VARCHAR(20) DEFAULT 'in_progress',
    error_message TEXT,
    error_code INTEGER,
    rate_limit_reset_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ====================================================================
-- WEB CRAWL TABLES
-- ====================================================================

-- Crawl History
CREATE TABLE IF NOT EXISTS crawl_history (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(36) UNIQUE NOT NULL,
    url VARCHAR(2048) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status crawl_status DEFAULT 'pending' NOT NULL,
    error_message VARCHAR(1024)
);

CREATE INDEX IF NOT EXISTS idx_crawl_history_request_id ON crawl_history(request_id);

-- Crawl Result
CREATE TABLE IF NOT EXISTS crawl_result (
    id SERIAL PRIMARY KEY,
    crawl_history_id INTEGER UNIQUE NOT NULL REFERENCES crawl_history(id) ON DELETE CASCADE,
    title VARCHAR(512),
    information TEXT,
    language VARCHAR(10),
    reviews_json JSON DEFAULT '[]',
    comments_json JSON DEFAULT '[]',
    blog_sections_json JSON DEFAULT '[]',
    agency_info_json JSON,
    detected_sections JSON DEFAULT '[]',
    crawl_strategy VARCHAR(20) DEFAULT 'single',
    extraction_strategy VARCHAR(20) DEFAULT 'llm'
);

-- ====================================================================
-- ASCA EXTRACTION TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS asca_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL DEFAULT 'youtube_comment',
    raw_text TEXT NOT NULL,
    aspects JSONB NOT NULL DEFAULT '[]',
    overall_score FLOAT NOT NULL DEFAULT 0.0,
    meta JSONB NOT NULL DEFAULT '{}',
    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    approved_result JSONB,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by VARCHAR(255),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_asca_source_unique ON asca_extractions(source_id, source_type);
CREATE INDEX IF NOT EXISTS idx_asca_pending ON asca_extractions(is_approved, is_deleted);
CREATE INDEX IF NOT EXISTS idx_asca_source_id ON asca_extractions(source_id);

-- ====================================================================
-- INTENTION TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS intentions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL DEFAULT 'youtube_comment',
    raw_text TEXT NOT NULL,
    intention_type intention_type,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_intentions_source_unique ON intentions(source_id, source_type);
CREATE INDEX IF NOT EXISTS idx_intentions_type ON intentions(intention_type);
CREATE INDEX IF NOT EXISTS idx_intentions_source_id ON intentions(source_id);

-- ====================================================================
-- LOCATION EXTRACTION TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS location_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL DEFAULT 'youtube_comment',
    raw_text TEXT NOT NULL,
    locations JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_location_source_unique ON location_extractions(source_id, source_type);
CREATE INDEX IF NOT EXISTS idx_location_source_id ON location_extractions(source_id);

-- ====================================================================
-- TARGETED ABSA TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS targeted_absa_results (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(255) NOT NULL,
    source_text TEXT,
    aspect VARCHAR(100) NOT NULL,
    sentiment VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    correction VARCHAR(50),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_targeted_absa_source_id ON targeted_absa_results(source_id);

-- ====================================================================
-- TRAVELING TYPE TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS traveling_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL DEFAULT 'youtube_comment',
    raw_text TEXT NOT NULL,
    traveling_type traveling_type,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_traveling_types_source_unique ON traveling_types(source_id, source_type);
CREATE INDEX IF NOT EXISTS idx_traveling_type ON traveling_types(traveling_type);
CREATE INDEX IF NOT EXISTS idx_traveling_types_source_id ON traveling_types(source_id);

-- ====================================================================
-- DONE
-- ====================================================================
SELECT 'All tables created successfully!' as status;
