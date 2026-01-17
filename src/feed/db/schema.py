"""Database schema definitions."""

# SQL schema for RSS posts table
CREATE_POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS rss_posts (
    id SERIAL PRIMARY KEY,
    link VARCHAR(2048) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    pub_date VARCHAR(255),
    media_urls JSONB,
    feed_title VARCHAR(500),
    feed_link VARCHAR(2048),
    is_processed BOOLEAN DEFAULT FALSE NOT NULL,
    is_event BOOLEAN,
    classification_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    processed_at TIMESTAMP
);
"""

# Create indexes for common queries
CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_rss_posts_link ON rss_posts(link);
CREATE INDEX IF NOT EXISTS idx_rss_posts_is_processed ON rss_posts(is_processed);
CREATE INDEX IF NOT EXISTS idx_rss_posts_is_event ON rss_posts(is_event);
CREATE INDEX IF NOT EXISTS idx_rss_posts_created_at ON rss_posts(created_at);
"""
