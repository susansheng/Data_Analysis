#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML报告生成器 - 生成交互式可视化网页
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path


def generate_html_report(data_file, output_file=None, min_click_threshold=10):
    """
    生成交互式HTML报告

    Args:
        data_file: 数据文件路径
        output_file: 输出HTML文件路径
        min_click_threshold: 最小点击量阈值
    """
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

    # 准备图表数据
    trend_dates = [d.strftime('%m-%d') for d in date_analysis['日期'].tail(15)]
    trend_ctr = date_analysis['ctr'].tail(15).tolist()
    trend_click_cvr = date_analysis['click_cvr'].tail(15).tolist()
    trend_order_cvr = date_analysis['order_cvr'].tail(15).tolist()

    top10_labels = top_modules['点击事件名称'].head(10).tolist()
    top10_ctr = top_modules['点击率(CTR)'].head(10).tolist()
    top10_click_cvr = top_modules['点击转化率'].head(10).tolist()
    top10_order_cvr = top_modules['下单转化率'].head(10).tolist()

    # 生成HTML
    if output_file is None:
        output_file = f"funnel_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 模块转化效能深度分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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

        header p {{
            font-size: 1.1em;
            opacity: 0.9;
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
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.2);
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

        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 40px;
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

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

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}

        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}

        .badge-info {{
            background: #d1ecf1;
            color: #0c5460;
        }}

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

        @media (max-width: 768px) {{
            .content {{
                padding: 20px;
            }}

            .metrics-grid {{
                grid-template-columns: 1fr;
            }}

            header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 模块转化效能深度分析报告</h1>
            <p>数据驱动的业务洞察 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
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

            <!-- 趋势图表 -->
            <div class="section">
                <h2 class="section-title">📈 核心指标趋势分析（最近15天）</h2>
                <div class="chart-container">
                    <canvas id="trendChart"></canvas>
                </div>
            </div>

            <!-- Top 10 对比图 -->
            <div class="section">
                <h2 class="section-title">🏆 Top 10 模块效能对比</h2>
                <div class="chart-container">
                    <canvas id="top10Chart"></canvas>
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

        # 根据点击率设置徽章
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
                                <td style="text-align: right;"><span class="badge {badge_class}">{row['点击率(CTR)']}%</span></td>
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
            <p>🤖 本报告由数据分析工具自动生成</p>
            <p style="margin-top: 5px;">数据清洗规则: 剔除点击量 &lt; {min_click_threshold} 的长尾数据 | 剔除点击 &gt; 曝光的异常数据</p>
        </div>
    </div>

    <script>
        // 趋势图表
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        new Chart(trendCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(trend_dates)},
                datasets: [
                    {{
                        label: '点击率 (CTR)',
                        data: {json.dumps(trend_ctr)},
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }},
                    {{
                        label: '点击转化率',
                        data: {json.dumps(trend_click_cvr)},
                        borderColor: 'rgb(247, 147, 26)',
                        backgroundColor: 'rgba(247, 147, 26, 0.1)',
                        tension: 0.4,
                        fill: true
                    }},
                    {{
                        label: '下单转化率',
                        data: {json.dumps(trend_order_cvr)},
                        borderColor: 'rgb(46, 213, 115)',
                        backgroundColor: 'rgba(46, 213, 115, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                    }},
                    title: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Top 10 对比图
        const top10Ctx = document.getElementById('top10Chart').getContext('2d');
        new Chart(top10Ctx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([label[:15] + '...' if len(label) > 15 else label for label in top10_labels])},
                datasets: [
                    {{
                        label: '点击率 (CTR)',
                        data: {json.dumps(top10_ctr)},
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgb(102, 126, 234)',
                        borderWidth: 2
                    }},
                    {{
                        label: '点击转化率',
                        data: {json.dumps(top10_click_cvr)},
                        backgroundColor: 'rgba(247, 147, 26, 0.8)',
                        borderColor: 'rgb(247, 147, 26)',
                        borderWidth: 2
                    }},
                    {{
                        label: '下单转化率',
                        data: {json.dumps(top10_order_cvr)},
                        backgroundColor: 'rgba(46, 213, 115, 0.8)',
                        borderColor: 'rgb(46, 213, 115)',
                        borderWidth: 2
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✓ HTML报告已生成: {output_file}")
    return output_file


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python generate_html_report.py <数据文件路径> [输出文件路径]")
        sys.exit(1)

    data_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    generate_html_report(data_file, output_file)
