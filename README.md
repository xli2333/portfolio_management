# 🚀智能证券投资组合管理系统

> **AI 驱动的智能投顾平台**
> 版本: 2.0.0 | 架构: React + Flask + Supabase | AI: Google Gemini

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
- **云端存储**：Supabase Storage 安全存储

### 📝 深度研报生成
- **AI 自动生成**：基于在线搜索的信息，选定AI模型生成深度分析报告
- **PDF 导出**：专业格式的研究报告
- **多维度分析**：技术面、基本面、市场情绪综合评估

### 👥 多用户系统
- **邮箱注册**：Supabase 认证系统
- **数据隔离**：RLS (Row Level Security) 确保数据安全
- **会话管理**：自动登录状态保持
- **安全登出**：完整的认证生命周期管理

---

## 🏗️ 技术架构

### 后端 (Backend)
- **框架**：Flask 3.0+
- **语言**：Python 3.12+
- **数据库**：Supabase PostgreSQL
- **AI 模型**：Google Gemini 2.0 Flash
- **数据源**：AKShare (财经数据)、yfinance (美股数据)
- **技术分析**：TA-Lib, Pandas, NumPy
- **PDF 生成**：ReportLab, PyPDF2

### 前端 (Frontend)
- **框架**：React 18 + TypeScript
- **构建工具**：Vite 5.0+
- **UI 框架**：Tailwind CSS
- **图表库**：Lightweight Charts, Recharts
- **图标**：Lucide React
- **认证**：Supabase Auth

### 云端部署
- **前端托管**：Vercel
- **后端服务**：Render (Docker)
- **数据库**：Supabase (PostgreSQL)
- **文件存储**：Supabase Storage

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

### 完整部署指南

请查看以下文档获取详细的部署步骤：

1. **[云端部署指南](./CLOUD_DEPLOYMENT_GUIDE.md)** - 完整的 9 步部署教程
2. **[部署检查清单](./DEPLOYMENT_CHECKLIST.md)** - 快速检查清单
3. **[Supabase 配置](./SUPABASE_SETUP.md)** - 数据库初始化指南

### 快速部署摘要

#### Supabase 数据库设置
1. 创建 Supabase 项目
2. 在 SQL Editor 中执行 `supabase_init.sql`
3. 复制 Project URL 和 anon public key

#### Render 后端部署
1. 连接 GitHub 仓库
2. 选择 Docker 运行时
3. 设置环境变量：
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
├── analyzer.py                # 技术分析引擎
├── advanced_indicators.py     # 高级技术指标
├── advanced_signals.py        # 高级交易信号
├── data_fetcher.py           # 数据获取服务
├── indicators.py             # 基础技术指标
├── portfolio_service.py      # 投资组合服务
├── knowledge_service.py      # 知识库服务
├── report_generator.py       # 深度研报生成器
├── web_app.py               # Flask 主应用
├── requirements.txt         # Python 依赖
├── Dockerfile              # Docker 配置
├── supabase_init.sql       # 数据库初始化脚本
├── .env.example            # 环境变量模板
├── client/                 # 前端应用
│   ├── src/
│   │   ├── components/     # React 组件
│   │   │   ├── Auth.tsx           # 认证组件
│   │   │   ├── Dashboard.tsx      # 仪表盘
│   │   │   ├── Analyzer.tsx       # 技术分析
│   │   │   ├── StockChat.tsx      # AI 投顾对话
│   │   │   ├── StockKnowledgeBase.tsx  # 知识库
│   │   │   └── ...
│   │   ├── App.tsx         # 主应用
│   │   └── main.tsx        # 入口文件
│   ├── package.json
│   └── vite.config.ts
└── knowledge_base/         # 知识库文档存储
```

---

## 🎯 核心功能说明

### 1. 投资组合管理
- 添加持仓时自动获取实时价格
- 支持美股 (如 AAPL, TSLA) 和 A 股 (如 300308, 600519)
- 自动计算持仓成本、当前市值、收益率
- 手动刷新数据按钮，避免频繁请求

### 2. 技术分析
- 多种技术指标可选
- 主图指标：MA, SuperTrend, Ichimoku Cloud
- 副图指标：MACD, RSI, KDJ
- 交易信号自动识别并标注

### 3. AI 智能投顾
- 基于 Google Gemini 2.0 Flash 模型
- 支持上下文对话
- 自动加载用户持仓信息
- 可针对具体股票提问

### 4. 知识库
- 上传 PDF 研报
- AI 基于文档内容回答问题
- 支持多个股票分类管理
- 文档列表查看和删除

### 5. 深度研报
- AI 自动分析历史数据
- 生成包含技术指标、趋势分析的 PDF 报告
- 支持下载保存

---

## 🔐 安全特性

### Row Level Security (RLS)
- 数据库级别的访问控制
- 用户只能访问自己的数据
- 防止跨用户数据泄露

### 环境变量管理
- 敏感信息不提交到 Git
- `.gitignore` 保护 `.env` 文件
- 生产环境使用平台环境变量

### 认证系统
- Supabase Auth 邮箱验证
- 会话令牌自动刷新
- 安全的登出机制

---

## 📊 数据来源

- **美股数据**：yfinance (Yahoo Finance API)
- **A股数据**：AKShare (开源财经数据接口)
- **AI 分析**：Google Gemini 2.0 Flash
- **技术指标**：TA-Lib + 自定义算法

---

## 🛠️ 开发说明

### 主要依赖

**后端**：
- Flask 3.0.0 - Web 框架
- google-genai 1.54.0 - Google AI SDK
- supabase 2.12.0 - Supabase 客户端
- pandas 2.2.0 - 数据处理
- akshare 1.15.14 - A 股数据
- yfinance 0.2.48 - 美股数据

**前端**：
- React 18.3.1
- TypeScript 5.6.2
- Vite 5.4.2
- @supabase/supabase-js 2.39.3
- lightweight-charts 4.2.0

### 开发工具
- VS Code
- Python 虚拟环境
- Node.js 包管理器

---

## ⚠️ 注意事项

1. **API Key 安全**：
   - 不要将 `.env` 文件提交到 Git
   - 不要在代码中硬编码 API Key
   - 使用环境变量管理敏感信息

2. **数据延迟**：
   - 免费数据源可能有延迟
   - 不适用于高频交易

3. **API 限制**：
   - 避免高频请求数据接口
   - 使用手动刷新而非自动刷新

4. **Render 免费计划**：
   - 15 分钟无活动会自动休眠
   - 首次唤醒可能需要 30-60 秒

---

## 📝 更新日志

### v2.0.0 (2025-12-10)
- ✨ 新增 AI 智能投顾功能 (Google Gemini)
- ✨ 新增知识库管理系统
- ✨ 新增深度研报生成器
- ✨ 新增多用户认证系统 (Supabase Auth)
- ✨ 新增数据隔离和 RLS 安全策略
- 🐛 修复 Dashboard 状态丢失问题
- 🐛 修复数据过度刷新问题
- 📦 支持 Docker 容器化部署
- 📦 支持 Vercel + Render + Supabase 云端部署

### v1.0.0
- 基础投资组合管理功能
- 技术分析和指标计算
- 可视化图表展示

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系方式

如有问题或建议，请通过 GitHub Issues 联系。

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
