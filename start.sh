#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# 加载环境变量
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 如果虚拟环境不存在则自动创建并安装依赖
if [ ! -d ".venv" ]; then
    echo ">>> 首次运行，创建虚拟环境..."
    python3 -m venv .venv
    source .venv/bin/activate
    .venv/bin/pip install --upgrade pip -q
    .venv/bin/pip install -e . -q
    echo ">>> 依赖安装完成"
else
    source .venv/bin/activate
fi

# 如果没有模拟数据则自动生成
DATA_DIR="$HOME/.racing-coach/data"
if [ ! -d "$DATA_DIR" ] || [ -z "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then
    echo ">>> 生成模拟数据..."
    python3 -m racing_coach.main generate-mock --laps 5 --track "Monza" --car "Ferrari 488 GT3"
fi

# 构建前端（如果 dist 不存在）
if [ ! -d "ui/dist" ]; then
    echo ">>> 构建前端..."
    cd ui
    npm install -q
    npm run build
    cd ..
    # 同步到后端静态文件目录
    rm -rf src/racing_coach/ui/dist
    cp -r ui/dist src/racing_coach/ui/dist
fi

echo ">>> 启动服务 http://127.0.0.1:8000"
python3 -m racing_coach.main serve
