-- 数据库表结构设计

-- 上传文件表
CREATE TABLE uploads (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_data BYTEA NOT NULL,
    file_size INTEGER NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 分析报告表
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
    report_html TEXT NOT NULL,
    data_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_uploads_created_at ON uploads(created_at DESC);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX idx_reports_upload_id ON reports(upload_id);
