#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全本地化的HTML报告生成器 - 无需任何外部依赖
使用纯CSS实现数据可视化
"""

import pandas as pd
from datetime import datetime
from pathlib import Path


def generate_offline_html_report(data_file, output_file=None, min_click_threshold=10):
    """
    生成完全离线的HTML报告（无任何外部依赖）

    Args:
        data_file: 数据文件路径
        output_file: 输出HTML文件路径
        min_click_threshold: 最小点击量阈值
    """
    # 转换为字符串处理
    data_file = str(data_file)

    # 加载数据
    print(f"正在加载数据: {data_file}")
    if data_file.endswith('.xlsx') or data_file.endswith('.xls'):
        df = pd.read_excel(data_file)
    elif data_file.endswith('.csv'):
        df = pd.read_csv(data_file)
    else:
        raise ValueError("不支持的文件格式")

    # 数据清洗
    original_count = len(df)
    df = df[df['点击UV(SUM)'] >= min_click_threshold]
    df = df[df['点击UV(SUM)'] <= df['页面UV(SUM)']]
    print(f"数据清洗: {original_count} -> {len(df)} 条记录")

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

    # 日期趋势分析
    df['日期'] = pd.to_datetime(df['日期'])
    date_analysis = df.groupby('日期').apply(
        lambda x: pd.Series({
            'ctr': round((x['点击UV(SUM)'].sum() / x['页面UV(SUM)'].sum() * 100), 2),
            'click_cvr': round((x['点击用户提交单(SUM)'].sum() / x['点击UV(SUM)'].sum() * 100), 2),
            'order_cvr': round((x['点击用户预订单(SUM)'].sum() / x['点击UV(SUM)'].sum() * 100), 2)
        }), include_groups=False
    ).reset_index()

    # 准备趋势数据（最近15天）
    trend_data = date_analysis.tail(15)

    # 生成HTML
    if output_file is None:
        output_file = f"funnel_analysis_offline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 模块转化效能深度分析报告（完全离线版）</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
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

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        header .badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            margin-top: 10px;
            font-size: 0.9em;
        }}

        .content {{
            padding: 40px;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
        }}

        .metric-label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .metric-subtitle {{
            font-size: 0.85em;
            color: #888;
            margin-top: 8px;
        }}

        .section {{
            margin-bottom: 50px;
        }}

        .section-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-left: 5px solid #667eea;
            padding-left: 15px;
        }}

        /* 纯CSS条形图 */
        .bar-chart {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .bar-item {{
            margin-bottom: 20px;
        }}

        .bar-label {{
            font-size: 0.9em;
            color: #555;
            margin-bottom: 5px;
            display: flex;
            justify-content: space-between;
        }}

        .bar-wrapper {{
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }}

        .bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-weight: bold;
            font-size: 0.85em;
            transition: width 1s ease-out;
        }}

        .bar-fill.ctr {{ background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); }}
        .bar-fill.cvr {{ background: linear-gradient(90deg, #f7931a 0%, #f5576c 100%); }}
        .bar-fill.order {{ background: linear-gradient(90deg, #2ed573 0%, #1e90ff 100%); }}

        /* 趋势线图（纯CSS） */
        .trend-chart {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .trend-legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 20px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
        }}

        .legend-color {{
            width: 20px;
            height: 4px;
            border-radius: 2px;
        }}

        .trend-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(60px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }}

        .trend-point {{
            text-align: center;
        }}

        .trend-bars {{
            height: 150px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            gap: 2px;
        }}

        .trend-bar {{
            border-radius: 3px;
            min-height: 2px;
        }}

        .trend-date {{
            font-size: 0.75em;
            color: #666;
            margin-top: 5px;
        }}

        /* 表格样式 */
        .table-container {{
            overflow-x: auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}

        tbody tr:hover {{
            background: #f5f7fa;
        }}

        .rank {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 50%;
            width: 35px;
            height: 35px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }}

        .rank.top3 {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}

        .badge-pill {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-info {{ background: #d1ecf1; color: #0c5460; }}

        .insights {{
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            border-radius: 15px;
            padding: 30px;
            margin-top: 30px;
        }}

        .insight-item {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .insight-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 10px;
        }}

        .insight-content {{
            color: #555;
            line-height: 1.8;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }}

        .offline-badge {{
            background: #2ecc71;
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
        }}

        @media (max-width: 768px) {{
            .content {{ padding: 20px; }}
            .metrics-grid {{ grid-template-columns: 1fr; }}
            header h1 {{ font-size: 1.8em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 模块转化效能深度分析报告</h1>
            <p>数据驱动的业务洞察 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <div class="badge">
                <span class="offline-badge">🔒 完全离线 · 数据本地化</span>
            </div>
            <p style="margin-top: 10px; font-size: 0.95em;">数据来源: {Path(data_file).name} | 分析记录: {len(df):,} 条</p>
        </header>

        <div class="content">
            <!-- 核心指标卡片 -->
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">点击率 CTR</div>
                    <div class="metric-value">{ctr}%</div>
                    <div class="metric-subtitle">总曝光 {total_exposure:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">点击转化率</div>
                    <div class="metric-value">{click_cvr}%</div>
                    <div class="metric-subtitle">总点击 {total_click:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">下单转化率</div>
                    <div class="metric-value">{order_cvr}%</div>
                    <div class="metric-subtitle">总下单 {total_order:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">分析周期</div>
                    <div class="metric-value">{len(date_analysis)}</div>
                    <div class="metric-subtitle">天数</div>
                </div>
            </div>

            <!-- 趋势图 -->
            <div class="section">
                <h2 class="section-title">📈 核心指标趋势分析（最近15天）</h2>
                <div class="trend-chart">
                    <div class="trend-legend">
                        <div class="legend-item">
                            <div class="legend-color" style="background: #667eea;"></div>
                            <span>点击率 (CTR)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #f7931a;"></div>
                            <span>点击转化率</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: #2ed573;"></div>
                            <span>下单转化率</span>
                        </div>
                    </div>
                    <div class="trend-grid">
"""

    # 添加趋势数据点
    max_val = max(trend_data['ctr'].max(), trend_data['click_cvr'].max(), trend_data['order_cvr'].max())
    for _, row in trend_data.iterrows():
        date_str = row['日期'].strftime('%m-%d')
        ctr_height = (row['ctr'] / max_val * 100) if max_val > 0 else 0
        cvr_height = (row['click_cvr'] / max_val * 100) if max_val > 0 else 0
        order_height = (row['order_cvr'] / max_val * 100) if max_val > 0 else 0

        html_content += f"""
                        <div class="trend-point">
                            <div class="trend-bars">
                                <div class="trend-bar" style="background: #667eea; height: {ctr_height}%;" title="CTR: {row['ctr']}%"></div>
                                <div class="trend-bar" style="background: #f7931a; height: {cvr_height}%;" title="点击CVR: {row['click_cvr']}%"></div>
                                <div class="trend-bar" style="background: #2ed573; height: {order_height}%;" title="下单CVR: {row['order_cvr']}%"></div>
                            </div>
                            <div class="trend-date">{date_str}</div>
                        </div>
"""

    html_content += """
                    </div>
                </div>
            </div>

            <!-- Top 10 对比图 -->
            <div class="section">
                <h2 class="section-title">🏆 Top 10 模块效能对比</h2>
                <div class="bar-chart">
"""

    # 添加Top 10条形图
    top10 = top_modules.head(10)
    max_ctr = top10['点击率(CTR)'].max()

    for _, row in top10.iterrows():
        name = row['点击事件名称']
        if len(name) > 20:
            name = name[:20] + '...'

        width_ctr = (row['点击率(CTR)'] / max_ctr * 100) if max_ctr > 0 else 0
        width_cvr = (row['点击转化率'] / max_ctr * 100) if max_ctr > 0 else 0
        width_order = (row['下单转化率'] / max_ctr * 100) if max_ctr > 0 else 0

        html_content += f"""
                    <div class="bar-item">
                        <div class="bar-label">
                            <span><strong>{name}</strong></span>
                        </div>
                        <div class="bar-wrapper">
                            <div class="bar-fill ctr" style="width: {width_ctr}%;">{row['点击率(CTR)']}%</div>
                        </div>
                        <div class="bar-wrapper" style="height: 20px; margin-top: 3px;">
                            <div class="bar-fill cvr" style="width: {width_cvr}%; font-size: 0.75em;">{row['点击转化率']}%</div>
                        </div>
                        <div class="bar-wrapper" style="height: 20px; margin-top: 3px;">
                            <div class="bar-fill order" style="width: {width_order}%; font-size: 0.75em;">{row['下单转化率']}%</div>
                        </div>
                    </div>
"""

    html_content += """
                </div>
            </div>

            <!-- Top 50 榜单表格 -->
            <div class="section">
                <h2 class="section-title">🎯 Top 50 高点击率模块榜单</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th style="text-align: center;">排名</th>
                                <th>模块名称</th>
                                <th style="text-align: right;">曝光人数</th>
                                <th style="text-align: right;">点击人数</th>
                                <th style="text-align: right;">点击率</th>
                                <th style="text-align: right;">点击转化率</th>
                                <th style="text-align: right;">下单转化率</th>
                            </tr>
                        </thead>
                        <tbody>
"""

    # 添加表格行
    for idx, row in top_modules.iterrows():
        rank = idx + 1
        rank_class = 'top3' if rank <= 3 else ''

        ctr_val = row['点击率(CTR)']
        if ctr_val >= 50:
            badge_class = 'badge-success'
        elif ctr_val >= 20:
            badge_class = 'badge-info'
        else:
            badge_class = 'badge-warning'

        html_content += f"""
                            <tr>
                                <td style="text-align: center;"><span class="rank {rank_class}">{rank}</span></td>
                                <td><strong>{row['点击事件名称']}</strong></td>
                                <td style="text-align: right;">{row['曝光人数']:,}</td>
                                <td style="text-align: right;">{row['点击人数']:,}</td>
                                <td style="text-align: right;"><span class="badge-pill {badge_class}">{row['点击率(CTR)']}%</span></td>
                                <td style="text-align: right;">{row['点击转化率']}%</td>
                                <td style="text-align: right;">{row['下单转化率']}%</td>
                            </tr>
"""

    # 业务洞察
    click_loss = 100 - ctr
    convert_loss = 100 - click_cvr
    order_loss = 100 - order_cvr
    max_loss = max(click_loss, convert_loss, order_loss)

    if max_loss == click_loss:
        max_loss_stage = "曝光到点击"
        suggestions = [
            "优化模块视觉设计，提升吸引力",
            "调整模块位置，增加曝光质量",
            "A/B测试不同的文案和图片",
            "增强CTA按钮的视觉突出度"
        ]
    elif max_loss == convert_loss:
        max_loss_stage = "点击到转化"
        suggestions = [
            "优化填写页体验，简化流程",
            "检查页面加载速度",
            "增加信任背书和优惠提示",
            "优化表单填写体验"
        ]
    else:
        max_loss_stage = "转化到下单"
        suggestions = [
            "优化支付流程，减少支付摩擦",
            "检查价格策略和优惠券使用",
            "增加订单确认页的信息透明度",
            "提供多种支付方式选择"
        ]

    html_content += f"""
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 业务洞察 -->
            <div class="insights">
                <h2 class="section-title" style="color: white; border-left-color: white;">💡 业务洞察与优化建议</h2>

                <div class="insight-item">
                    <div class="insight-title">🔍 漏斗流失分析</div>
                    <div class="insight-content">
                        <p><strong>最大流失环节:</strong> {max_loss_stage} (流失率 {max_loss:.2f}%)</p>
                        <ul style="margin-top: 10px; padding-left: 20px;">
                            <li>曝光到点击: {click_loss:.2f}% 用户未点击</li>
                            <li>点击到转化: {convert_loss:.2f}% 用户点击后未提交订单</li>
                            <li>转化到下单: {order_loss:.2f}% 用户提交后未完成预订</li>
                        </ul>
                    </div>
                </div>

                <div class="insight-item">
                    <div class="insight-title">🎯 优化建议</div>
                    <div class="insight-content">
                        <p><strong>针对 {max_loss_stage} 环节:</strong></p>
                        <ul style="margin-top: 10px; padding-left: 20px;">
                            {"".join([f"<li>{s}</li>" for s in suggestions])}
                        </ul>
                    </div>
                </div>

                <div class="insight-item">
                    <div class="insight-title">🏆 高价值模块推荐</div>
                    <div class="insight-content">
                        <p>以下模块点击率最高，建议重点推广:</p>
                        <ul style="margin-top: 10px; padding-left: 20px;">
"""

    for _, row in top_modules.head(5).iterrows():
        html_content += f"""
                            <li><strong>{row['点击事件名称']}</strong>: CTR {row['点击率(CTR)']}%, 下单CVR {row['下单转化率']}%</li>
"""

    html_content += f"""
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>🤖 本报告由数据分析工具自动生成 | <span class="offline-badge">🔒 100% 本地运行 · 无云端依赖</span></p>
            <p style="margin-top: 10px;">数据清洗规则: 剔除点击量 &lt; {min_click_threshold} 的长尾数据 | 剔除点击 &gt; 曝光的异常数据</p>
            <p style="margin-top: 5px; font-size: 0.85em; color: #999;">所有数据均在本地处理，未上传任何服务器</p>
        </div>
    </div>
</body>
</html>
"""

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✓ 完全离线的HTML报告已生成: {output_file}")
    print(f"✓ 无任何外部依赖，可在无网络环境下打开")
    return output_file


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python generate_offline_report.py <数据文件路径> [输出文件路径]")
        sys.exit(1)

    data_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    generate_offline_html_report(data_file, output_file)
