#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 数据库工具模块
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from contextlib import contextmanager

# 从环境变量获取数据库连接
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

@contextmanager
def get_db_connection():
    """获取数据库连接（上下文管理器）"""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def save_upload(filename, file_data, file_size):
    """保存上传的文件到数据库"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO uploads (filename, file_data, file_size)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (filename, file_data, file_size)
            )
            result = cur.fetchone()
            return result['id']


def get_upload(upload_id):
    """获取上传的文件"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM uploads WHERE id = %s",
                (upload_id,)
            )
            return cur.fetchone()


def save_report(upload_id, report_html, data_info):
    """保存分析报告到数据库"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reports (upload_id, report_html, data_info)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (upload_id, report_html, json.dumps(data_info))
            )
            result = cur.fetchone()
            return result['id']


def get_report(report_id):
    """获取报告"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM reports WHERE id = %s",
                (report_id,)
            )
            return cur.fetchone()


def list_reports(limit=50):
    """列出最近的报告"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.id, r.created_at, r.data_info, u.filename
                FROM reports r
                JOIN uploads u ON r.upload_id = u.id
                ORDER BY r.created_at DESC
                LIMIT %s
                """,
                (limit,)
            )
            return cur.fetchall()


def init_database():
    """初始化数据库表（如果不存在）"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 创建 uploads 表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    file_data BYTEA NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建 reports 表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
                    report_html TEXT NOT NULL,
                    data_info JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_uploads_created_at
                ON uploads(created_at DESC)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_reports_created_at
                ON reports(created_at DESC)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_reports_upload_id
                ON reports(upload_id)
            """)
