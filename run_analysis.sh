#!/bin/bash
# 数据分析工具 - 一键运行脚本

echo "=================================================="
echo "📊 数据分析工具 - 一键运行"
echo "🔒 100% 本地运行，数据不上传云端"
echo "=================================================="
echo ""

# 检查参数
if [ $# -eq 0 ]; then
    echo "❌ 错误: 请提供数据文件路径"
    echo ""
    echo "使用方法:"
    echo "  ./run_analysis.sh <数据文件路径>"
    echo ""
    echo "示例:"
    echo "  ./run_analysis.sh ~/Documents/数据.xlsx"
    echo ""
    exit 1
fi

DATA_FILE="$1"

# 检查文件是否存在
if [ ! -f "$DATA_FILE" ]; then
    echo "❌ 错误: 文件不存在 - $DATA_FILE"
    exit 1
fi

echo "📁 数据文件: $DATA_FILE"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 开始分析..."
echo ""

# 生成时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 运行完全离线的HTML报告生成
echo "1️⃣  生成可视化HTML报告（完全离线版）..."
python3 generate_offline_report.py "$DATA_FILE" "report_offline_${TIMESTAMP}.html"

echo ""
echo "2️⃣  生成Markdown文本报告..."
python3 funnel_analyzer.py "$DATA_FILE" -o "report_${TIMESTAMP}.md"

echo ""
echo "=================================================="
echo "✅ 分析完成！"
echo "=================================================="
echo ""
echo "📊 生成的报告:"
echo "  • HTML可视化报告: report_offline_${TIMESTAMP}.html"
echo "  • Markdown文本报告: report_${TIMESTAMP}.md"
echo ""
echo "💡 提示:"
echo "  • 双击HTML文件即可在浏览器中查看"
echo "  • 所有数据均在本地处理，未上传任何服务器"
echo "  • 可在无网络环境下打开报告"
echo ""

# 询问是否打开报告
read -p "是否立即打开HTML报告？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "report_offline_${TIMESTAMP}.html"
fi
