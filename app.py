#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析工具 - Web应用版本
本地运行的Web服务，通过浏览器访问，100%数据本地化
"""

from flask import Flask, render_template, request, send_file, jsonify, url_for
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename
import sys

# 导入分析功能
sys.path.append(str(Path(__file__).parent))
from generate_offline_report import generate_offline_html_report

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['REPORT_FOLDER'] = Path(__file__).parent / 'reports'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# 确保目录存在
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['REPORT_FOLDER'].mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传和分析"""
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({'error': '未选择文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式，请上传 .xlsx, .xls 或 .csv 文件'}), 400

        # 保存文件
        # 从原始文件名提取扩展名
        original_filename = file.filename
        if '.' in original_filename:
            file_ext = original_filename.rsplit('.', 1)[-1].lower()
        else:
            file_ext = ''

        # 生成安全的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{timestamp}.{file_ext}" if file_ext else f"{timestamp}_file"

        file_path = app.config['UPLOAD_FOLDER'] / saved_filename
        file.save(str(file_path))

        # 获取参数
        min_click = int(request.form.get('min_click', 10))

        # 生成报告
        report_filename = f"report_{timestamp}.html"
        report_path = app.config['REPORT_FOLDER'] / report_filename

        # 调用分析函数
        generate_offline_html_report(
            str(file_path),
            str(report_path),
            min_click_threshold=min_click
        )

        # 读取数据基本信息
        if file_path.suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(str(file_path))
        else:
            df = pd.read_csv(str(file_path))

        data_info = {
            'rows': len(df),
            'columns': len(df.columns),
            'filename': original_filename
        }

        # 返回成功响应
        return jsonify({
            'success': True,
            'report_url': url_for('view_report', filename=report_filename),
            'download_url': url_for('download_report', filename=report_filename),
            'data_info': data_info
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n❌ 错误详情:\n{error_details}")
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@app.route('/report/<filename>')
def view_report(filename):
    """在浏览器中查看报告"""
    report_path = app.config['REPORT_FOLDER'] / filename
    if not report_path.exists():
        return "报告不存在", 404
    return send_file(str(report_path))


@app.route('/download/<filename>')
def download_report(filename):
    """下载报告"""
    report_path = app.config['REPORT_FOLDER'] / filename
    if not report_path.exists():
        return "报告不存在", 404
    return send_file(str(report_path), as_attachment=True)


@app.route('/reports')
def list_reports():
    """列出所有历史报告"""
    reports = []
    for file in sorted(app.config['REPORT_FOLDER'].glob('*.html'), reverse=True):
        stat = file.stat()
        reports.append({
            'filename': file.name,
            'size': f"{stat.st_size / 1024:.1f} KB",
            'created': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'view_url': url_for('view_report', filename=file.name),
            'download_url': url_for('download_report', filename=file.name)
        })
    return jsonify(reports)


if __name__ == '__main__':
    # 支持环境变量 PORT，方便部署到云平台
    PORT = int(os.environ.get('PORT', 5000))

    print("\n" + "="*70)
    print("📊 数据分析工具 - Web版本")
    print("🔒 100% 本地运行 · 数据不上传云端")
    print("="*70)
    print("\n✅ 服务已启动！")
    print("\n🌐 请在浏览器中打开:")
    print(f"\n    http://localhost:{PORT}")
    print(f"\n或者:")
    print(f"\n    http://127.0.0.1:{PORT}")
    print("\n💡 提示:")
    print("  • 拖拽上传文件或点击选择")
    print("  • 所有数据在本地处理")
    print("  • 按 Ctrl+C 停止服务")
    print("\n" + "="*70 + "\n")

    # 使用 0.0.0.0 使其可以从外部访问（云部署需要）
    app.run(host='0.0.0.0', port=PORT, debug=False)
