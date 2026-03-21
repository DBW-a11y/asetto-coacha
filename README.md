# Racing Coach

赛车遥测分析 + AI 教练应用，适用于 Assetto Corsa / ACC。

通过采集赛车遥测数据（油门、刹车、速度、G 力、轮胎温度等），自动分析驾驶表现并借助 Claude AI 生成个性化驾驶建议。

## 功能特性

- **遥测采集** — 支持 Assetto Corsa 共享内存实时采集、模拟数据生成、Parquet 文件回放
- **数据存储** — Parquet 存储时序遥测数据，SQLite 存储会话/圈速元信息
- **驾驶分析** — 圈速指标、弯道检测（入弯/弯心/出弯速度）、驾驶评分（制动、油门、一致性、转向）
- **圈速对比** — 任意两圈 delta time 和速度差异对比
- **AI 教练** — 基于 Claude 的智能分析，生成中文驾驶改进建议（支持缓存）
- **可视化前端** — React + Plotly.js 图表，包含速度曲线、输入曲线、评分卡片、弯道明细

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.9+, FastAPI, Uvicorn |
| 数据处理 | Pandas, NumPy, SciPy, PyArrow |
| AI | Anthropic Claude API |
| 前端 | React 19, TypeScript, Vite, Plotly.js |
| 存储 | Parquet + SQLite |

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+

### 安装

```bash
# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 升级 pip 并安装 Python 依赖
pip install --upgrade pip
pip install -e .

# 安装前端依赖并构建
cd ui && npm install && npm run build && cd ..
```

### 运行

```bash
# 1. 生成模拟数据（首次使用）
python3 -m racing_coach.main generate-mock --laps 5 --track "Monza" --car "Ferrari 488 GT3"

# 2. 启动服务
python3 -m racing_coach.main serve
# 访问 http://127.0.0.1:8000
```

### 前端开发模式

```bash
cd ui && npm run dev
# 访问 http://localhost:5173（自动代理 API 到后端）
```

## CLI 命令

```bash
# 生成模拟遥测数据
python3 -m racing_coach.main generate-mock \
  --laps 5 \
  --rate 50 \
  --track "Monza" \
  --car "Ferrari 488 GT3"

# 启动 API 服务
python3 -m racing_coach.main serve

# 录制实时遥测（需 Assetto Corsa 运行中）
python3 -m racing_coach.main record \
  --track "Monza" \
  --car "Ferrari 488 GT3"

# 回放已录制的数据
python3 -m racing_coach.main record \
  --replay path/to/session.parquet \
  --track "Monza" \
  --car "Ferrari 488 GT3"
```

## API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/sessions/` | 会话列表 |
| GET | `/api/sessions/{id}` | 会话详情 |
| GET | `/api/telemetry/{id}` | 完整遥测数据 |
| GET | `/api/telemetry/{id}/lap/{n}` | 单圈遥测数据 |
| GET | `/api/analysis/{id}/lap/{n}` | 单圈分析（指标+评分+弯道） |
| GET | `/api/analysis/{id}/compare?lap1=X&lap2=Y` | 两圈对比 |
| GET | `/api/coaching/{id}/lap/{n}` | AI 教练建议 |
| WS | `/api/live/ws` | 实时遥测 WebSocket |

## 配置

配置文件位于 `config/default.toml`，主要配置项：

```toml
[general]
data_dir = "~/.racing-coach/data"   # 数据存储目录

[collector]
type = "mock"                        # 采集器类型: mock / ac / acc
sample_rate_hz = 100                 # 采样率

[coach]
model = "claude-sonnet-4-20250514"   # AI 模型
language = "zh-CN"                   # 教练语言

[api]
host = "127.0.0.1"
port = 8000
```

如需使用 AI 教练功能，请设置环境变量：

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

## 项目结构

```
src/racing_coach/
├── main.py              # CLI 入口
├── config.py            # 配置加载
├── collectors/          # 遥测采集（模拟/AC共享内存/回放）
├── storage/             # 存储层（Parquet + SQLite）
├── analysis/            # 分析算法（指标/弯道/评分/对比）
├── coach/               # AI 教练（Claude API + 提示词模板）
└── api/                 # FastAPI 路由

ui/src/
├── pages/               # 页面（会话列表/详情/圈速分析）
├── components/          # 组件（图表/评分卡/对比图）
└── api.ts               # 类型化 API 客户端
```

## License

MIT
