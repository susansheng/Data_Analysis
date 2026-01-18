#!/bin/bash
# 启动数据分析工具Web服务

echo "=================================================="
echo "📊 数据分析工具 - 启动Web服务"
echo "=================================================="
echo ""

# 检查Flask是否安装
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  检测到Flask未安装"
    echo "正在安装Flask..."
    pip3 install flask --quiet
    echo "✅ Flask安装完成"
    echo ""
fi

# 进入脚本所在目录
cd "$(dirname "$0")"

# 启动Flask应用
python3 app.py
