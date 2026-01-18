#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析工具 - 用户行为漏斗分析
基于曝光->点击->转化->下单的用户行为漏斗，精准计算核心指标并输出业务洞察
"""

import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path
from datetime import datetime


class FunnelAnalyzer:
    """漏斗分析核心类"""

    def __init__(self, file_path, min_click_threshold=10):
        """
        初始化分析器

        Args:
            file_path: 数据文件路径
            min_click_threshold: 最小点击量阈值，用于过滤长尾噪音
        """
        self.file_path = file_path
        self.min_click_threshold = min_click_threshold
        self.df = None
        self.report = []

    def load_data(self):
        """加载数据文件"""
        try:
            if self.file_path.endswith('.xlsx') or self.file_path.endswith('.xls'):
                self.df = pd.read_excel(self.file_path)
            elif self.file_path.endswith('.csv'):
                self.df = pd.read_csv(self.file_path)
            else:
                raise ValueError("不支持的文件格式，请使用 .xlsx, .xls 或 .csv 文件")

            print(f"✓ 成功加载数据: {len(self.df)} 行 × {len(self.df.columns)} 列")
            return True
        except Exception as e:
            print(f"✗ 数据加载失败: {str(e)}")
            return False

    def audit_and_clean(self):
        """步骤1: 数据审计与清洗"""
        print("\n" + "="*80)
        print("步骤1: 数据审计与清洗")
        print("="*80)

        # 字段映射识别
        print("\n📋 字段映射识别:")
        field_mapping = {
            '曝光人数': '页面UV(SUM)',
            '点击人数': '点击UV(SUM)',
            '转化人数（提交单）': '点击用户提交单(SUM)',
            '下单人数（预订单）': '点击用户预订单(SUM)'
        }

        for label, col in field_mapping.items():
            if col in self.df.columns:
                print(f"  ✓ {label}: {col}")
            else:
                print(f"  ✗ {label}: 字段缺失")

        # 数据清洗前的统计
        original_count = len(self.df)
        print(f"\n📊 原始数据: {original_count} 条记录")

        # 1. 剔除点击量 < 阈值的长尾数据
        self.df = self.df[self.df['点击UV(SUM)'] >= self.min_click_threshold]
        after_click_filter = len(self.df)
        print(f"  ✓ 剔除点击量 < {self.min_click_threshold} 的数据: {original_count - after_click_filter} 条")

        # 2. 剔除异常数据（点击 > 曝光）
        self.df = self.df[self.df['点击UV(SUM)'] <= self.df['页面UV(SUM)']]
        after_anomaly_filter = len(self.df)
        print(f"  ✓ 剔除点击 > 曝光的异常数据: {after_click_filter - after_anomaly_filter} 条")

        # 3. 检查缺失值
        null_counts = self.df.isnull().sum()
        if null_counts.sum() > 0:
            print(f"\n⚠️  发现缺失值:")
            for col, count in null_counts[null_counts > 0].items():
                print(f"    {col}: {count} 个缺失值")
        else:
            print(f"\n✓ 无缺失值")

        print(f"\n✓ 清洗后数据: {len(self.df)} 条记录")

    def calculate_metrics(self, group_df):
        """
        计算核心指标

        Args:
            group_df: 分组数据框

        Returns:
            dict: 包含各项指标的字典
        """
        total_exposure = group_df['页面UV(SUM)'].sum()
        total_click = group_df['点击UV(SUM)'].sum()
        total_convert = group_df['点击用户提交单(SUM)'].sum()
        total_order = group_df['点击用户预订单(SUM)'].sum()

        # 避免除零错误
        ctr = (total_click / total_exposure * 100) if total_exposure > 0 else 0
        click_cvr = (total_convert / total_click * 100) if total_click > 0 else 0
        order_cvr = (total_order / total_click * 100) if total_click > 0 else 0

        return {
            'exposure': total_exposure,
            'click': total_click,
            'convert': total_convert,
            'order': total_order,
            'ctr': round(ctr, 2),
            'click_cvr': round(click_cvr, 2),
            'order_cvr': round(order_cvr, 2)
        }

    def multi_dimensional_analysis(self):
        """步骤2: 多维交叉分析"""
        print("\n" + "="*80)
        print("步骤2: 多维交叉分析")
        print("="*80)

        # 1. 整体漏斗计算
        print("\n📊 整体指标计算:")
        overall_metrics = self.calculate_metrics(self.df)

        print(f"  曝光人数: {overall_metrics['exposure']:,}")
        print(f"  点击人数: {overall_metrics['click']:,}")
        print(f"  转化人数: {overall_metrics['convert']:,}")
        print(f"  下单人数: {overall_metrics['order']:,}")
        print(f"  ✓ 点击率 (CTR): {overall_metrics['ctr']}%")
        print(f"  ✓ 点击转化率 (Click CVR): {overall_metrics['click_cvr']}%")
        print(f"  ✓ 下单转化率 (Order CVR): {overall_metrics['order_cvr']}%")

        self.overall_metrics = overall_metrics

        # 2. 按点击事件分析（模块级分析）
        print("\n📊 按点击事件分组分析:")
        event_analysis = self.df.groupby('点击事件名称').apply(
            lambda x: pd.Series({
                '曝光人数': x['页面UV(SUM)'].sum(),
                '点击人数': x['点击UV(SUM)'].sum(),
                '转化人数': x['点击用户提交单(SUM)'].sum(),
                '下单人数': x['点击用户预订单(SUM)'].sum(),
            })
        ).reset_index()

        # 计算指标
        event_analysis['点击率(CTR)'] = (
            event_analysis['点击人数'] / event_analysis['曝光人数'] * 100
        ).round(2)
        event_analysis['点击转化率'] = (
            event_analysis['转化人数'] / event_analysis['点击人数'] * 100
        ).round(2)
        event_analysis['下单转化率'] = (
            event_analysis['下单人数'] / event_analysis['点击人数'] * 100
        ).round(2)

        # 按点击率降序排列
        event_analysis = event_analysis.sort_values('点击率(CTR)', ascending=False)

        self.event_analysis = event_analysis
        print(f"  ✓ 识别到 {len(event_analysis)} 个不同的点击事件")

        # 3. 按平台分析
        if '平台' in self.df.columns:
            print("\n📊 按平台分组分析:")
            platform_analysis = self.df.groupby('平台').apply(
                lambda x: pd.Series(self.calculate_metrics(x))
            )
            print(platform_analysis[['ctr', 'click_cvr', 'order_cvr']])
            self.platform_analysis = platform_analysis

        # 4. 按日期趋势分析
        if '日期' in self.df.columns:
            print("\n📊 按日期趋势分析:")
            self.df['日期'] = pd.to_datetime(self.df['日期'])
            date_analysis = self.df.groupby('日期').apply(
                lambda x: pd.Series(self.calculate_metrics(x))
            )
            self.date_analysis = date_analysis
            print(f"  ✓ 时间跨度: {self.df['日期'].min()} 至 {self.df['日期'].max()}")
            print(f"  ✓ 共 {len(date_analysis)} 天数据")

    def generate_top_list(self, top_n=50):
        """生成Top N高点击率模块榜单"""
        print(f"\n🏆 生成 Top {top_n} 高点击率模块榜单")

        # 获取前N条记录
        self.top_modules = self.event_analysis.head(top_n).copy()

        # 添加排名
        self.top_modules.insert(0, '排名', range(1, len(self.top_modules) + 1))

        print(f"  ✓ 已生成 Top {len(self.top_modules)} 榜单")

        return self.top_modules

    def generate_visualizations(self):
        """步骤3: 生成数据可视化代码（Mermaid）"""
        print("\n" + "="*80)
        print("步骤3: 数据可视化")
        print("="*80)

        visualizations = []

        # 1. 漏斗转化趋势图
        if hasattr(self, 'date_analysis') and len(self.date_analysis) > 0:
            # 取最近10天的数据
            recent_dates = self.date_analysis.tail(10)

            mermaid_line = "```mermaid\n"
            mermaid_line += "%%{init: {'theme':'base'}}%%\n"
            mermaid_line += "xychart-beta\n"
            mermaid_line += "    title \"核心指标趋势 (最近10天)\"\n"
            mermaid_line += "    x-axis [" + ", ".join([f'"{d.strftime("%m-%d")}"' for d in recent_dates.index]) + "]\n"
            mermaid_line += "    y-axis \"转化率 (%)\" 0 --> 100\n"
            mermaid_line += "    line [" + ", ".join([str(v) for v in recent_dates['ctr'].values]) + "]\n"
            mermaid_line += "    line [" + ", ".join([str(v) for v in recent_dates['click_cvr'].values]) + "]\n"
            mermaid_line += "    line [" + ", ".join([str(v) for v in recent_dates['order_cvr'].values]) + "]\n"
            mermaid_line += "```\n"

            visualizations.append(("漏斗趋势图", mermaid_line))

        # 2. Top 10模块点击率对比
        if hasattr(self, 'top_modules'):
            top10 = self.top_modules.head(10)

            mermaid_bar = "```mermaid\n"
            mermaid_bar += "%%{init: {'theme':'base'}}%%\n"
            mermaid_bar += "xychart-beta\n"
            mermaid_bar += "    title \"Top 10 模块点击率对比\"\n"

            # 简化模块名称（取前10个字符）
            labels = [name[:10] + "..." if len(name) > 10 else name for name in top10['点击事件名称'].values]
            mermaid_bar += "    x-axis [" + ", ".join([f'"{label}"' for label in labels]) + "]\n"
            mermaid_bar += "    y-axis \"点击率 (%)\" 0 --> 100\n"
            mermaid_bar += "    bar [" + ", ".join([str(v) for v in top10['点击率(CTR)'].values]) + "]\n"
            mermaid_bar += "```\n"

            visualizations.append(("Top 10模块点击率", mermaid_bar))

        self.visualizations = visualizations
        print(f"  ✓ 生成 {len(visualizations)} 个可视化图表")

    def generate_insights(self):
        """步骤4: 归因与建议"""
        print("\n" + "="*80)
        print("步骤4: 归因与业务建议")
        print("="*80)

        insights = []

        # 1. 漏斗流失分析
        ctr = self.overall_metrics['ctr']
        click_cvr = self.overall_metrics['click_cvr']
        order_cvr = self.overall_metrics['order_cvr']

        # 找出最大流失环节
        click_loss = 100 - ctr
        convert_loss = 100 - click_cvr
        order_loss = 100 - order_cvr

        max_loss_stage = max(
            ('曝光到点击', click_loss),
            ('点击到转化', convert_loss),
            ('转化到下单', order_loss),
            key=lambda x: x[1]
        )

        insights.append({
            'title': '🔍 漏斗流失分析',
            'content': [
                f"最大流失环节: **{max_loss_stage[0]}**，流失率 {max_loss_stage[1]:.2f}%",
                f"- 曝光到点击: {click_loss:.2f}% 用户未点击",
                f"- 点击到转化: {convert_loss:.2f}% 用户点击后未提交订单",
                f"- 转化到下单: {order_loss:.2f}% 用户提交后未完成预订"
            ]
        })

        # 2. 高价值模块识别
        if hasattr(self, 'top_modules'):
            top5 = self.top_modules.head(5)
            insights.append({
                'title': '🏆 高价值模块推荐',
                'content': [
                    "以下模块点击率最高，建议重点推广:",
                    *[f"- **{row['点击事件名称']}**: CTR {row['点击率(CTR)']}%, 下单CVR {row['下单转化率']}%"
                      for _, row in top5.iterrows()]
                ]
            })

        # 3. 低效模块预警
        if hasattr(self, 'event_analysis'):
            # 找出点击率低但曝光量大的模块
            low_ctr = self.event_analysis[
                (self.event_analysis['点击率(CTR)'] < ctr * 0.5) &
                (self.event_analysis['曝光人数'] > self.event_analysis['曝光人数'].median())
            ].head(5)

            if len(low_ctr) > 0:
                insights.append({
                    'title': '⚠️ 低效模块预警',
                    'content': [
                        "以下模块曝光量大但点击率低，需优化:",
                        *[f"- **{row['点击事件名称']}**: CTR {row['点击率(CTR)']}% (曝光 {row['曝光人数']:,})"
                          for _, row in low_ctr.iterrows()]
                    ]
                })

        # 4. 优化建议
        insights.append({
            'title': '💡 业务优化建议',
            'content': [
                f"**针对{max_loss_stage[0]}环节流失:**",
            ]
        })

        if max_loss_stage[0] == '曝光到点击':
            insights[-1]['content'].extend([
                "- 优化模块视觉设计，提升吸引力",
                "- 调整模块位置，增加曝光质量",
                "- A/B测试不同的文案和图片"
            ])
        elif max_loss_stage[0] == '点击到转化':
            insights[-1]['content'].extend([
                "- 优化填写页体验，简化流程",
                "- 检查页面加载速度",
                "- 增加信任背书和优惠提示"
            ])
        else:
            insights[-1]['content'].extend([
                "- 优化支付流程，减少支付摩擦",
                "- 检查价格策略和优惠券使用",
                "- 增加订单确认页的信息透明度"
            ])

        self.insights = insights
        print(f"  ✓ 生成 {len(insights)} 条业务洞察")

    def generate_markdown_report(self, output_path=None):
        """生成完整的Markdown分析报告"""
        print("\n" + "="*80)
        print("生成分析报告")
        print("="*80)

        if output_path is None:
            output_path = f"funnel_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        report_lines = []

        # 标题
        report_lines.append("# 📊 模块转化效能深度分析报告\n")
        report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_lines.append(f"**数据来源**: {Path(self.file_path).name}\n")
        report_lines.append(f"**分析数据量**: {len(self.df):,} 条记录\n")
        report_lines.append("\n---\n\n")

        # 1. 核心指标总览
        report_lines.append("## 1. 📋 核心指标总览\n\n")
        report_lines.append("| 指标 | 数值 |\n")
        report_lines.append("| :--- | :--- |\n")
        report_lines.append(f"| **整体点击率 (CTR)** | **{self.overall_metrics['ctr']}%** |\n")
        report_lines.append(f"| **整体点击转化率 (Click CVR)** | **{self.overall_metrics['click_cvr']}%** |\n")
        report_lines.append(f"| **整体下单转化率 (Order CVR)** | **{self.overall_metrics['order_cvr']}%** |\n")
        report_lines.append(f"| 总曝光人数 | {self.overall_metrics['exposure']:,} |\n")
        report_lines.append(f"| 总点击人数 | {self.overall_metrics['click']:,} |\n")
        report_lines.append(f"| 总转化人数 | {self.overall_metrics['convert']:,} |\n")
        report_lines.append(f"| 总下单人数 | {self.overall_metrics['order']:,} |\n")
        report_lines.append("\n")

        # 2. Top 50 高点击率模块榜单
        report_lines.append("## 2. 🏆 Top 50 高点击率模块榜单\n\n")
        report_lines.append("按点击率降序排列，展示表现最优秀的模块:\n\n")

        # 生成表格
        report_lines.append("| 排名 | 模块名称 | 曝光人数 | 点击人数 | **点击率(CTR)** | 点击转化率 | 下单转化率 |\n")
        report_lines.append("| :---: | :--- | ---: | ---: | ---: | ---: | ---: |\n")

        for _, row in self.top_modules.iterrows():
            report_lines.append(
                f"| {row['排名']} "
                f"| {row['点击事件名称']} "
                f"| {row['曝光人数']:,} "
                f"| {row['点击人数']:,} "
                f"| **{row['点击率(CTR)']}%** "
                f"| {row['点击转化率']}% "
                f"| {row['下单转化率']}% |\n"
            )

        report_lines.append("\n")

        # 3. 数据可视化
        if hasattr(self, 'visualizations') and len(self.visualizations) > 0:
            report_lines.append("## 3. 📈 可视化看板\n\n")

            for viz_title, viz_code in self.visualizations:
                report_lines.append(f"### {viz_title}\n\n")
                report_lines.append(viz_code)
                report_lines.append("\n")

        # 4. 业务洞察与建议
        if hasattr(self, 'insights'):
            report_lines.append("## 4. 💡 业务洞察与优化建议\n\n")

            for insight in self.insights:
                report_lines.append(f"### {insight['title']}\n\n")
                for content in insight['content']:
                    report_lines.append(f"{content}\n")
                report_lines.append("\n")

        # 5. 附录
        report_lines.append("## 5. 📎 附录\n\n")
        report_lines.append("### 指标计算公式\n\n")
        report_lines.append("1. **模块点击率 (CTR)** = `(点击人数 / 曝光人数) × 100%`\n")
        report_lines.append("2. **点击转化率 (Click CVR)** = `(转化人数 / 点击人数) × 100%`\n")
        report_lines.append("3. **下单转化率 (Order CVR)** = `(下单人数 / 点击人数) × 100%`\n\n")

        report_lines.append("### 数据清洗规则\n\n")
        report_lines.append(f"- 剔除点击量 < {self.min_click_threshold} 的长尾数据\n")
        report_lines.append("- 剔除点击 > 曝光的异常数据\n")
        report_lines.append("- 所有指标保留2位小数\n\n")

        report_lines.append("---\n\n")
        report_lines.append("*🤖 本报告由数据分析工具自动生成*\n")

        # 写入文件
        report_content = "".join(report_lines)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"\n✓ 报告已生成: {output_path}")
        return output_path

    def run_analysis(self, output_path=None):
        """运行完整分析流程"""
        print("\n" + "="*80)
        print("🚀 开始数据分析")
        print("="*80)

        # 加载数据
        if not self.load_data():
            return False

        # 执行分析步骤
        self.audit_and_clean()
        self.multi_dimensional_analysis()
        self.generate_top_list()
        self.generate_visualizations()
        self.generate_insights()
        report_path = self.generate_markdown_report(output_path)

        print("\n" + "="*80)
        print("✅ 分析完成!")
        print("="*80)
        print(f"\n📄 报告位置: {report_path}")

        return True


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='数据分析工具 - 用户行为漏斗分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python funnel_analyzer.py data.xlsx
  python funnel_analyzer.py data.xlsx -o report.md
  python funnel_analyzer.py data.xlsx --min-click 20
        """
    )

    parser.add_argument('file', help='数据文件路径 (支持 .xlsx, .xls, .csv)')
    parser.add_argument('-o', '--output', help='输出报告文件路径 (默认自动生成)', default=None)
    parser.add_argument('--min-click', type=int, default=10,
                       help='最小点击量阈值，用于过滤长尾数据 (默认: 10)')

    args = parser.parse_args()

    # 检查文件是否存在
    if not Path(args.file).exists():
        print(f"✗ 错误: 文件不存在 - {args.file}")
        sys.exit(1)

    # 创建分析器并运行
    analyzer = FunnelAnalyzer(args.file, min_click_threshold=args.min_click)
    success = analyzer.run_analysis(args.output)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
