-- Smart Knowledge Repository Database Schema
-- Version: 1.0
-- Description: Complete schema for knowledge management system

-- Main documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT UNIQUE,
    content_type TEXT NOT NULL,
    domain TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    word_count INTEGER DEFAULT 0,
    char_count INTEGER DEFAULT 0,
    reading_time_minutes INTEGER DEFAULT 0,
    metadata JSON DEFAULT '{}',
    scrape_metadata JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted'))
);

-- Categories for organization
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER,
    color TEXT DEFAULT '#6366f1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- Document-category relationships
CREATE TABLE IF NOT EXISTS document_categories (
    document_id INTEGER,
    category_id INTEGER,
    confidence REAL DEFAULT 1.0,
    assigned_by TEXT DEFAULT 'auto',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (document_id, category_id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- Scraping jobs tracking
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,
    job_type TEXT DEFAULT 'web_scrape',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    total_urls INTEGER DEFAULT 0,
    processed_urls INTEGER DEFAULT 0,
    failed_urls INTEGER DEFAULT 0,
    settings JSON DEFAULT '{}',
    error_log TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search analytics
CREATE TABLE IF NOT EXISTS search_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    scope TEXT,
    results_count INTEGER DEFAULT 0,
    avg_relevance_score REAL DEFAULT 0.0,
    response_time_ms INTEGER DEFAULT 0,
    user_session TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation history
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    sources JSON DEFAULT '[]',
    scope TEXT,
    confidence REAL DEFAULT 0.0,
    feedback INTEGER, -- 1 for positive, -1 for negative, NULL for no feedback
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced conversation management
CREATE TABLE IF NOT EXISTS conversation_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    context_window_size INTEGER DEFAULT 4000,
    total_messages INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL,
    role TEXT CHECK (role IN ('user', 'assistant')) NOT NULL,
    content TEXT NOT NULL,
    sources JSON DEFAULT '[]',
    metadata JSON DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES conversation_threads(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_domain ON documents(domain);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_search_analytics_timestamp ON search_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_threads_session_id ON conversation_threads(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_thread_id ON conversation_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_timestamp ON conversation_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_document_categories_document_id ON document_categories(document_id);
CREATE INDEX IF NOT EXISTS idx_document_categories_category_id ON document_categories(category_id);

-- Insert default categories
INSERT OR IGNORE INTO categories (name, description, color) VALUES
('Technology', 'Technology-related content including AI, software, and programming', '#3b82f6'),
('Business', 'Business strategy, management, and finance content', '#10b981'),
('Science', 'Scientific research, experiments, and analysis', '#8b5cf6'),
('Healthcare', 'Medical and health-related information', '#ef4444'),
('Education', 'Educational content and learning materials', '#f59e0b'),
('General', 'Uncategorized or general knowledge content', '#6b7280');

-- Create triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_documents_timestamp 
    AFTER UPDATE ON documents
    FOR EACH ROW
BEGIN
    UPDATE documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
