# 学习通智能作业批改系统

## 📖 项目简介
一个基于 FastAPI + Vue 3 的智能批改系统，帮助教师自动收集作业、识别附件内容、AI评分、人工复核、导出成绩。

## 🛠 技术栈
- **后端**: Python + FastAPI + PostgreSQL + MinIO
- **前端**: Vue 3 + Element Plus + Vite
- **AI**: PaddleOCR + 大模型 API

## ✨ 核心功能
- 多模态附件识别（图片OCR / 文档解析 / 代码提取）
- 大模型智能评分 + 可解释评语
- 教师复核与分数修正
- Excel 成绩导出

## 🚀 本地运行
1. 启动 Docker: `docker-compose up -d`
2. 安装后端依赖: `cd backend && pip install -r requirements.txt`
3. 启动后端: `uvicorn app.main:app --reload --port 8000`
4. 启动前端: `cd frontend && npm install && npm run dev`
5. 访问: `http://localhost:5173`
