#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析工具 - Vercel Serverless 版本
使用 PostgreSQL 存储数据
"""

from flask import Flask, render_template, request, jsonify, make_response
import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from io import BytesIO
import traceback

# 添加父目录到路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# 尝试导入数据库工具
try:
    from api.db import save_upload, get_upload, save_report, get_report, list_reports, init_database
    DB_AVAILABLE = True
except Exception as e:
    print(f"警告: 数据库模块导入失败: {e}")
    DB_AVAILABLE = False

# Flask 应用配置
template_folder = parent_dir / 'templates'
static_folder = parent_dir / 'static'

print(f"Template folder: {template_folder}, exists: {template_folder.exists()}")
print(f"Static folder: {static_folder}, exists: {static_folder.exists()}")

app = Flask(__name__,
            template_folder=str(template_folder),
            static_folder=str(static_folder))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# 检查环境变量
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
if not DATABASE_URL:
    print("警告: 未设置 DATABASE_URL 环境变量")
else:
    print(f"数据库连接已配置: {DATABASE_URL[:30]}...")

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def analyze_data_from_bytes(file_data, filename, min_click_threshold=10):
    """从字节数据分析并生成报告"""
    # 读取数据
    file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if file_ext in ['xlsx', 'xls']:
        df = pd.read_excel(BytesIO(file_data))
    elif file_ext == 'csv':
        df = pd.read_csv(BytesIO(file_data))
    else:
        raise ValueError("不支持的文件格式")

    # 数据清洗
    original_count = len(df)
    df = df[df['点击UV(SUM)'] >= min_click_threshold]
    df = df[df['点击UV(SUM)'] <= df['页面UV(SUM)']]

    # 计算整体指标
    total_exposure = df['页面UV(SUM)'].sum()
    total_click = df['点击UV(SUM)'].sum()
    total_convert = df['点击用户提交单(SUM)'].sum()
    total_order = df['点击用户预订单(SUM)'].sum()

    ctr = round((total_click / total_exposure * 100) if total_exposure > 0 else 0, 2)
    click_cvr = round((total_convert / total_click * 100) if total_click > 0 else 0, 2)
    order_cvr = round((total_order / total_click * 100) if total_click > 0 else 0, 2)

    # 按点击事件分组分析
    event_analysis = df.groupby('点击事件名称').agg({
        '页面UV(SUM)': 'sum',
        '点击UV(SUM)': 'sum',
        '点击用户提交单(SUM)': 'sum',
        '点击用户预订单(SUM)': 'sum'
    }).reset_index()

    event_analysis.columns = ['点击事件名称', '曝光人数', '点击人数', '转化人数', '下单人数']
    event_analysis['点击率(CTR)'] = (event_analysis['点击人数'] / event_analysis['曝光人数'] * 100).round(2)
    event_analysis['点击转化率'] = (event_analysis['转化人数'] / event_analysis['点击人数'] * 100).round(2)
    event_analysis['下单转化率'] = (event_analysis['下单人数'] / event_analysis['点击人数'] * 100).round(2)
    event_analysis = event_analysis.sort_values('点击率(CTR)', ascending=False)

    # 获取Top 50
    top_modules = event_analysis.head(50)

    # 生成简化的HTML报告
    report_html = generate_simple_html_report(
        filename, len(df), original_count,
        ctr, click_cvr, order_cvr,
        total_exposure, total_click, total_convert, total_order,
        top_modules, min_click_threshold
    )

    # 返回报告和数据信息
    data_info = {
        'rows': len(df),
        'columns': len(df.columns),
        'filename': filename,
        'ctr': ctr,
        'click_cvr': click_cvr,
        'order_cvr': order_cvr
    }

    return report_html, data_info


def generate_simple_html_report(filename, rows, original_rows, ctr, click_cvr, order_cvr,
                                 total_exposure, total_click, total_convert, total_order,
                                 top_modules, min_click_threshold):
    """生成简化的HTML报告"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 数据分析报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .content {{ padding: 40px; }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
        }}
        .metric-label {{ font-size: 0.9em; color: #666; margin-bottom: 10px; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        tr:hover {{ background: #f5f7fa; }}
        .footer {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 数据分析报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>数据源: {filename} | 分析记录: {rows:,} / {original_rows:,} 条</p>
        </header>
        <div class="content">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">点击率 CTR</div>
                    <div class="metric-value">{ctr}%</div>
                    <div style="font-size: 0.85em; color: #888;">曝光 {total_exposure:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">点击转化率</div>
                    <div class="metric-value">{click_cvr}%</div>
                    <div style="font-size: 0.85em; color: #888;">点击 {total_click:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">下单转化率</div>
                    <div class="metric-value">{order_cvr}%</div>
                    <div style="font-size: 0.85em; color: #888;">下单 {total_order:,}</div>
                </div>
            </div>
            <h2 style="margin-bottom: 20px;">🎯 Top 50 高点击率模块</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>模块名称</th>
                        <th>曝光</th>
                        <th>点击</th>
                        <th>点击率</th>
                        <th>转化率</th>
                    </tr>
                </thead>
                <tbody>
"""

    for idx, row in top_modules.iterrows():
        rank = idx + 1
        html += f"""
                    <tr>
                        <td>{rank}</td>
                        <td><strong>{row['点击事件名称']}</strong></td>
                        <td>{row['曝光人数']:,}</td>
                        <td>{row['点击人数']:,}</td>
                        <td>{row['点击率(CTR)']}%</td>
                        <td>{row['点击转化率']}%</td>
                    </tr>
"""

    html += f"""
                </tbody>
            </table>
        </div>
        <div class="footer">
            <p>🤖 数据分析工具 | 部署在 Vercel</p>
            <p style="margin-top: 10px; font-size: 0.9em;">数据清洗规则: 点击量 ≥ {min_click_threshold}</p>
        </div>
    </div>
</body>
</html>
"""
    return html


@app.route('/')
def index():
    """主页"""
    try:
        return render_template('index.html')
    except Exception as e:
        error_msg = f"错误: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return f"<h1>服务器错误</h1><pre>{error_msg}</pre>", 500


@app.route('/health')
def health():
    """健康检查端点"""
    status = {
        'status': 'ok',
        'database': DB_AVAILABLE,
        'database_url_set': bool(DATABASE_URL),
        'template_folder': str(template_folder),
        'template_exists': template_folder.exists()
    }
    return jsonify(status)


@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传和分析"""
    try:
        # 检查数据库是否可用
        if not DB_AVAILABLE:
            return jsonify({'error': '数据库未配置，请联系管理员'}), 500

        # 检查文件
        if 'file' not in request.files:
            return jsonify({'error': '未选择文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式，请上传 .xlsx, .xls 或 .csv 文件'}), 400

        # 读取文件数据
        file_data = file.read()
        file_size = len(file_data)
        original_filename = file.filename

        # 保存到数据库
        upload_id = save_upload(original_filename, file_data, file_size)

        # 获取参数
        min_click = int(request.form.get('min_click', 10))

        # 分析数据并生成报告
        report_html, data_info = analyze_data_from_bytes(file_data, original_filename, min_click)

        # 保存报告到数据库
        report_id = save_report(upload_id, report_html, data_info)

        # 返回成功响应
        return jsonify({
            'success': True,
            'report_id': report_id,
            'report_url': f'/report/{report_id}',
            'download_url': f'/download/{report_id}',
            'data_info': data_info
        })

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"\n❌ 错误详情:\n{error_details}")
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@app.route('/report/<int:report_id>')
def view_report(report_id):
    """在浏览器中查看报告"""
    try:
        report = get_report(report_id)
        if not report:
            return "报告不存在", 404

        response = make_response(report['report_html'])
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    except Exception as e:
        return f"错误: {str(e)}", 500


@app.route('/download/<int:report_id>')
def download_report(report_id):
    """下载报告"""
    try:
        report = get_report(report_id)
        if not report:
            return "报告不存在", 404

        response = make_response(report['report_html'])
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=report_{report_id}.html'
        return response
    except Exception as e:
        return f"错误: {str(e)}", 500


@app.route('/reports')
def list_all_reports():
    """列出所有历史报告"""
    try:
        reports = list_reports(50)
        result = []
        for report in reports:
            result.append({
                'id': report['id'],
                'filename': report['filename'],
                'created': report['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'data_info': report['data_info'],
                'view_url': f'/report/{report["id"]}',
                'download_url': f'/download/{report["id"]}'
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/init-db')
def init_db():
    """初始化数据库（仅用于首次部署）"""
    try:
        if not DB_AVAILABLE:
            return jsonify({'error': '数据库模块未加载'}), 500

        if not DATABASE_URL:
            return jsonify({'error': 'DATABASE_URL 环境变量未设置'}), 500

        init_database()
        return jsonify({'success': True, 'message': '数据库初始化成功'})
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"数据库初始化错误: {error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500


# Vercel 入口点
def handler(request):
    """Vercel serverless 函数入口"""
    with app.request_context(request.environ):
        return app.full_dispatch_request()


# 本地测试
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
