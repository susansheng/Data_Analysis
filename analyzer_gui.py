#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析工具 - 图形界面版本
提供友好的文件选择界面，方便快速分析不同数据文件
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
from pathlib import Path
from datetime import datetime
import threading


class FunnelAnalyzerGUI:
    """数据分析工具图形界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("📊 数据分析工具 - 用户行为漏斗分析")
        self.root.geometry("700x600")
        self.root.resizable(False, False)

        # 获取脚本所在目录
        self.script_dir = Path(__file__).parent

        # 设置样式
        self.setup_styles()

        # 创建界面
        self.create_widgets()

        # 居中显示窗口
        self.center_window()

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 配置颜色
        self.bg_color = "#f5f7fa"
        self.accent_color = "#667eea"
        self.root.configure(bg=self.bg_color)

    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """创建界面组件"""

        # 标题区域
        title_frame = tk.Frame(self.root, bg=self.accent_color, height=100)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="📊 数据分析工具",
            font=("Arial", 24, "bold"),
            bg=self.accent_color,
            fg="white"
        )
        title_label.pack(pady=10)

        subtitle_label = tk.Label(
            title_frame,
            text="🔒 100% 本地运行 · 数据不上传云端",
            font=("Arial", 11),
            bg=self.accent_color,
            fg="white"
        )
        subtitle_label.pack()

        # 主内容区域
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 文件选择区域
        file_frame = tk.LabelFrame(
            main_frame,
            text="1️⃣  选择数据文件",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        file_frame.pack(fill=tk.X, pady=(0, 20))

        # 文件路径显示
        self.file_path_var = tk.StringVar(value="未选择文件")
        file_path_label = tk.Label(
            file_frame,
            textvariable=self.file_path_var,
            font=("Arial", 10),
            bg="white",
            fg="#666",
            relief=tk.SUNKEN,
            anchor="w",
            padx=10,
            pady=10
        )
        file_path_label.pack(fill=tk.X, padx=10, pady=(10, 5))

        # 选择文件按钮
        select_btn = tk.Button(
            file_frame,
            text="📁 选择文件",
            font=("Arial", 11, "bold"),
            bg=self.accent_color,
            fg="white",
            activebackground="#5568d3",
            activeforeground="white",
            cursor="hand2",
            padx=20,
            pady=10,
            command=self.select_file
        )
        select_btn.pack(pady=(5, 10))

        # 支持格式提示
        format_label = tk.Label(
            file_frame,
            text="支持格式: .xlsx, .xls, .csv",
            font=("Arial", 9),
            bg=self.bg_color,
            fg="#999"
        )
        format_label.pack(pady=(0, 10))

        # 参数设置区域
        param_frame = tk.LabelFrame(
            main_frame,
            text="2️⃣  分析参数",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        param_frame.pack(fill=tk.X, pady=(0, 20))

        # 最小点击量阈值
        threshold_frame = tk.Frame(param_frame, bg=self.bg_color)
        threshold_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            threshold_frame,
            text="最小点击量阈值:",
            font=("Arial", 10),
            bg=self.bg_color
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.threshold_var = tk.IntVar(value=10)
        threshold_spinbox = tk.Spinbox(
            threshold_frame,
            from_=1,
            to=100,
            textvariable=self.threshold_var,
            font=("Arial", 10),
            width=10
        )
        threshold_spinbox.pack(side=tk.LEFT)

        tk.Label(
            threshold_frame,
            text="（过滤点击量小于此值的数据）",
            font=("Arial", 9),
            bg=self.bg_color,
            fg="#999"
        ).pack(side=tk.LEFT, padx=(10, 0))

        # 报告类型选择
        report_frame = tk.LabelFrame(
            main_frame,
            text="3️⃣  选择报告类型",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        report_frame.pack(fill=tk.X, pady=(0, 20))

        self.html_var = tk.BooleanVar(value=True)
        self.md_var = tk.BooleanVar(value=False)

        html_check = tk.Checkbutton(
            report_frame,
            text="🌐 HTML可视化报告（推荐）",
            variable=self.html_var,
            font=("Arial", 10),
            bg=self.bg_color,
            activebackground=self.bg_color
        )
        html_check.pack(anchor="w", padx=10, pady=(10, 5))

        md_check = tk.Checkbutton(
            report_frame,
            text="📄 Markdown文本报告",
            variable=self.md_var,
            font=("Arial", 10),
            bg=self.bg_color,
            activebackground=self.bg_color
        )
        md_check.pack(anchor="w", padx=10, pady=(5, 10))

        # 生成按钮
        generate_btn = tk.Button(
            main_frame,
            text="🚀 生成分析报告",
            font=("Arial", 14, "bold"),
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            activeforeground="white",
            cursor="hand2",
            padx=30,
            pady=15,
            command=self.generate_report
        )
        generate_btn.pack(pady=(0, 20))

        # 进度显示区域
        self.status_var = tk.StringVar(value="等待开始...")
        status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#666"
        )
        status_label.pack()

        # 进度条
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=400
        )
        self.progress.pack(pady=10)

        # 底部信息
        footer_label = tk.Label(
            main_frame,
            text="💡 提示: 生成的报告会自动保存在工具目录下",
            font=("Arial", 9),
            bg=self.bg_color,
            fg="#999"
        )
        footer_label.pack(side=tk.BOTTOM, pady=(20, 0))

    def select_file(self):
        """选择数据文件"""
        file_path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[
                ("Excel文件", "*.xlsx *.xls"),
                ("CSV文件", "*.csv"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            self.file_path_var.set(file_path)
            self.status_var.set(f"已选择: {Path(file_path).name}")

    def generate_report(self):
        """生成分析报告"""
        file_path = self.file_path_var.get()

        # 验证文件
        if file_path == "未选择文件" or not file_path:
            messagebox.showwarning("提示", "请先选择数据文件！")
            return

        if not Path(file_path).exists():
            messagebox.showerror("错误", "文件不存在！")
            return

        # 验证报告类型
        if not self.html_var.get() and not self.md_var.get():
            messagebox.showwarning("提示", "请至少选择一种报告类型！")
            return

        # 在新线程中执行，避免界面卡死
        thread = threading.Thread(target=self._generate_report_thread, args=(file_path,))
        thread.daemon = True
        thread.start()

    def _generate_report_thread(self, file_path):
        """在后台线程中生成报告"""
        try:
            # 显示进度
            self.progress.start()
            self.status_var.set("正在分析数据，请稍候...")

            threshold = self.threshold_var.get()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            generated_files = []

            # 生成HTML报告
            if self.html_var.get():
                self.status_var.set("正在生成HTML可视化报告...")
                html_output = self.script_dir / f"report_offline_{timestamp}.html"

                result = subprocess.run(
                    [
                        "python3",
                        str(self.script_dir / "generate_offline_report.py"),
                        file_path,
                        str(html_output)
                    ],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    generated_files.append(("HTML报告", html_output))

            # 生成Markdown报告
            if self.md_var.get():
                self.status_var.set("正在生成Markdown文本报告...")
                md_output = self.script_dir / f"report_{timestamp}.md"

                result = subprocess.run(
                    [
                        "python3",
                        str(self.script_dir / "funnel_analyzer.py"),
                        file_path,
                        "-o", str(md_output),
                        "--min-click", str(threshold)
                    ],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    generated_files.append(("Markdown报告", md_output))

            # 停止进度条
            self.progress.stop()

            if generated_files:
                # 显示成功消息
                self.status_var.set("✅ 报告生成完成！")

                # 构建消息
                msg = "分析报告已生成：\n\n"
                for name, path in generated_files:
                    msg += f"• {name}: {path.name}\n"
                msg += "\n是否立即打开报告？"

                if messagebox.askyesno("成功", msg):
                    # 打开第一个报告
                    subprocess.run(["open", str(generated_files[0][1])])

            else:
                self.status_var.set("❌ 生成失败")
                messagebox.showerror("错误", "报告生成失败，请检查数据格式是否正确。")

        except Exception as e:
            self.progress.stop()
            self.status_var.set("❌ 发生错误")
            messagebox.showerror("错误", f"发生错误：{str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = FunnelAnalyzerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
