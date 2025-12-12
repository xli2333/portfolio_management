# 🚀智能证券投资组合管理系统

> **AI 驱动的智能投顾平台**
> 版本: 2.1.0 | 架构: React + Flask + Supabase | AI: Google Gemini (Deep Research)

一个集成技术分析、AI 投顾、知识库管理和深度研报生成的现代化投资组合管理平台。支持多用户注册、数据隔离、云端部署。

---

## ✨ 核心特性

### 📊 投资组合管理
- **实时行情监控**：自动获取美股、A股实时数据
- **持仓管理**：添加、编辑、删除持仓，自动计算盈亏
- **技术指标分析**：MA, MACD, RSI, KDJ, SuperTrend, Ichimoku Cloud 等
- **交易信号识别**：金叉/死叉、趋势反转、超买超卖预警
- **可视化图表**：专业级 K 线图，支持多指标叠加

### 🤖 AI 智能投顾
- **Google Gemini 驱动**：基于Gemini 2.5 flash/pro 模型
- **智能对话**：针对持仓股票进行智能问答
- **上下文感知**：自动加载用户持仓和历史数据
- **专业分析**：提供技术面、基本面综合建议
- **图像识别**：识别股票走势图像，并提供当前价格下的综合建议

### 📚 知识库管理
- **文档上传**：支持 PDF 研报上传和管理
- **对话导出**：支持 多轮对话中选定对话的导出与长久保存
- **智能检索**：基于选定文档内容的 AI 问答
- **多股票支持**：按股票代码分类管理文档
- **云端存储**：Supabase Storage / Render Disk 安全存储

### ⚡ 顶级深度报告 (Ultra Deep Report)
- **Deep Research API**：集成 Google 官方 Deep Research 能力
- **三种模式**：个股深度分析 (STOCK)、宏观经济分析 (MACRO)、量化策略设计 (STRATEGY)
- **异步任务系统**：后台自动执行耗时任务，完美适配云端环境（解决 Serverless 超时问题）
- **万字长文**：生成 5000+ 字的专业级研报，包含大量数据引用和参考文献

### 👥 多用户系统
- **邮箱注册**：Supabase 认证系统
- **数据隔离**：RLS (Row Level Security) 确保数据安全
- **会话管理**：自动登录状态保持
- **安全登出**：完整的认证生命周期管理

---

## 🏗️ 技术架构

### 后端 (Backend)
- **框架**：Flask 3.0+ (支持异步任务)
- **语言**：Python 3.12+
- **数据库**：Supabase PostgreSQL
- **AI 模型**：Google Gemini 2.0 Flash / Deep Research
- **数据源**：AKShare (财经数据)、yfinance (美股数据)
- **技术分析**：TA-Lib, Pandas, NumPy
- **PDF 生成**：ReportLab, PyPDF2
- **任务管理**：本地持久化 JSON 存储 (Task Manager)

### 前端 (Frontend)
- **框架**：React 18 + TypeScript
- **构建工具**：Vite 5.0+
- **UI 框架**：Tailwind CSS
- **图表库**：Lightweight Charts, Recharts
- **图标**：Lucide React
- **认证**：Supabase Auth
- **交互**：实时轮询 (Polling) 任务状态

### 云端部署
- **前端托管**：Vercel
- **后端服务**：Render (Docker + Persistent Disk)
- **数据库**：Supabase (PostgreSQL)
- **文件存储**：Supabase Storage / Render Persistent Disk

---

## 📦 快速开始

### 环境要求
- Python 3.12+
- Node.js 18.0+
- Git

### 本地开发

#### 1. 克隆项目
```bash
git clone https://github.com/xli2333/portfolio_management.git
cd portfolio_management
```

#### 2. 后端配置

创建 `.env` 文件：
```bash
# Google Gemini API (必须)
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase 配置 (生产环境必须)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_public_key_here

# 服务器端口 (可选，默认 5000)
PORT=5000
```

安装依赖并启动：
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动后端
python web_app.py
```

后端将运行在 `http://localhost:5000`

#### 3. 前端配置

创建 `client/.env` 文件：
```bash
VITE_API_URL=http://localhost:5000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_public_key_here
```

安装依赖并启动：
```bash
cd client
npm install
npm run dev
```

前端将运行在 `http://localhost:5173`

---

## ☁️ 云端部署

### 快速部署摘要

#### Supabase 数据库设置
1. 创建 Supabase 项目
2. 在 SQL Editor 中执行 `supabase_init.sql`
3. 复制 Project URL 和 anon public key

#### Render 后端部署
1. 连接 GitHub 仓库
2. 选择 Docker 运行时
3. 开启 Persistent Disk (挂载路径 `/app/knowledge_base`) 以保存任务状态和 PDF 文件
4. 设置环境变量：
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `GEMINI_API_KEY`
   - `PORT=10000`

#### Vercel 前端部署
1. 导入 GitHub 仓库
2. 设置 Root Directory 为 `client`
3. 设置环境变量：
   - `VITE_API_URL` (Render 后端 URL)
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`

---

## 📁 项目结构

```
portfolio_management/
├── analyst_agent.py           # AI 分析师代理
├── deep_research_agent.py     # Deep Research 代理 (New)
├── task_manager.py            # 异步任务管理器 (New)
├── analyzer.py                # 技术分析引擎
├── advanced_indicators.py     # 高级技术指标
├── data_fetcher.py           # 数据获取服务
├── portfolio_service.py      # 投资组合服务
├── knowledge_service.py      # 知识库服务
├── report_generator.py       # 深度研报生成器
├── web_app.py               # Flask 主应用
├── requirements.txt         # Python 依赖
├── Dockerfile              # Docker 配置
├── client/                 # 前端应用
│   ├── src/
│   │   ├── components/     # React 组件
│   │   │   ├── StockKnowledgeBase.tsx  # 知识库 (Updated)
│   │   │   └── ...
└── knowledge_base/         # 知识库文档存储
```

---

## 📝 更新日志

### v2.1.0 (2025-12-12)
- ✨ **重磅更新**：新增 "顶级深度报告" (Ultra Deep Report) 功能
- ⚡ **架构升级**：后端引入异步任务队列，解决云端部署超时问题
- 🔄 **交互优化**：前端支持任务状态实时轮询
- 📝 **文档更新**：更新部署文档适配 Render Persistent Disk

### v2.0.0 (2025-12-10)
- ✨ 新增 AI 智能投顾功能 (Google Gemini)
- ✨ 新增知识库管理系统
- ✨ 新增深度研报生成器
- ✨ 新增多用户认证系统 (Supabase Auth)
- ✨ 新增数据隔离和 RLS 安全策略

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**