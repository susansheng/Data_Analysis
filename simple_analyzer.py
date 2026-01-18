#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的文件上传分析工具 - 无需Web服务
直接在命令行中选择文件并分析
"""

import os
import sys
from pathlib import Path
from generate_offline_report import generate_offline_html_report

def list_files():
    """列出当前目录和常用目录的数据文件"""
    print("\n" + "="*70)
    print("📁 请选择要分析的数据文件")
    print("="*70)

    # 搜索常用位置的数据文件
    search_paths = [
        Path.cwd(),
        Path.home() / "Documents",
        Path.home() / "Downloads",
        Path.home() / "Desktop"
    ]

    files = []
    for search_path in search_paths:
        if search_path.exists():
            for ext in ['*.xlsx', '*.xls', '*.csv']:
                files.extend(search_path.glob(ext))
                files.extend(search_path.glob(f'**/{ext}'))

    # 去重并按修改时间排序
    files = sorted(set(files), key=lambda x: x.stat().st_mtime, reverse=True)

    return files[:20]  # 只显示最近的20个文件


def main():
    """主函数"""
    print("\n" + "="*70)
    print("📊 数据分析工具")
    print("🔒 100% 本地运行 · 数据不上传云端")
    print("="*70)

    while True:
        print("\n请选择操作:")
        print("  1. 输入文件路径进行分析")
        print("  2. 从最近文件中选择")
        print("  3. 退出")

        choice = input("\n请输入选项 (1/2/3): ").strip()

        if choice == '3':
            print("\n👋 再见！")
            break

        elif choice == '1':
            file_path = input("\n请输入文件完整路径: ").strip()

            # 去除引号
            file_path = file_path.strip('"').strip("'")

            if not os.path.exists(file_path):
                print(f"\n❌ 错误: 文件不存在 - {file_path}")
                continue

            analyze_file(file_path)

        elif choice == '2':
            files = list_files()

            if not files:
                print("\n❌ 未找到数据文件")
                continue

            print("\n最近的数据文件:")
            for i, file in enumerate(files, 1):
                size = file.stat().st_size / 1024
                print(f"  {i}. {file.name} ({size:.1f} KB)")
                print(f"     位置: {file.parent}")

            try:
                file_num = int(input("\n请输入文件编号: ").strip())
                if 1 <= file_num <= len(files):
                    analyze_file(str(files[file_num - 1]))
                else:
                    print("\n❌ 无效的编号")
            except ValueError:
                print("\n❌ 请输入数字")

        else:
            print("\n❌ 无效的选项")


def analyze_file(file_path):
    """分析文件"""
    print("\n" + "="*70)
    print("🚀 开始分析")
    print("="*70)

    try:
        # 生成报告文件名
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"report_{timestamp}.html"

        # 执行分析
        print(f"\n📄 数据文件: {Path(file_path).name}")
        print(f"📊 正在分析...")

        generate_offline_html_report(file_path, output_file, min_click_threshold=10)

        print(f"\n✅ 分析完成！")
        print(f"\n📊 报告已生成: {output_file}")
        print(f"   位置: {Path(output_file).absolute()}")

        # 询问是否打开
        open_report = input("\n是否立即打开报告？(y/n): ").strip().lower()
        if open_report == 'y':
            import subprocess
            subprocess.run(['open', output_file])
            print("\n✅ 已在浏览器中打开报告")

        print("\n" + "="*70)

    except Exception as e:
        print(f"\n❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
        sys.exit(0)
