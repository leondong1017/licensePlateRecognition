# 车牌识别系统 设计文档

**日期：** 2026-03-30
**状态：** 已确认，待实现

---

## 1. 项目背景

用户上传图片或视频帧，系统自动识别其中的车牌信息，结果用于违章举报辅助。主要应用场景为国内道路，需覆盖中国大陆主流车牌类型。

---

## 2. 核心需求

| 需求 | 说明 |
|------|------|
| 图片/视频帧上传 | 支持 JPG、PNG、BMP，最大 20MB |
| 车牌识别 | 自动检测并识别画面中的车牌号、类型、位置 |
| 模糊图片处理 | 置信度 < 0.9 时自动触发超分辨率增强后重新识别 |
| 多车场景 | 检测到多辆车时，引导用户框选目标区域（ROI），仅识别框内车牌 |
| 历史记录 | 本地 SQLite 存储识别记录，支持筛选、查询、CSV 导出 |
| 视觉化车牌 | 识别结果以真实车牌配色渲染（蓝/绿渐变/黄/白），直观展示车牌类型 |

---

## 3. 技术选型

### 前端
- **框架：** Vue 3 + TypeScript + Vite
- **UI 组件库：** TDesign Vue Next（腾讯官方，原生 Vue 3 支持最成熟）
- **设计规范：** TDesign Design Token，主题色覆盖为黑白灰（主色 #1a1a1a）

### 后端
- **框架：** Python + FastAPI
- **识别引擎：** HyperLPR3（`pip install hyperlpr3`）
  - 准确率 95–97%（出入口/路面场景）
  - 支持 12 种中国大陆车牌类型
  - 推理时间 < 100ms/张（CPU）
- **超分引擎：** Real-ESRGAN（仅对低置信度车牌区域裁剪处理，CPU 耗时 1–4s）
- **数据库：** SQLite（通过 Python `sqlite3` 标准库直接操作）

### 部署
- 开发阶段：前端 `vite dev`（port 5173）+ 后端 `uvicorn`（port 8000）本地并行运行
- 后期：Docker Compose 打包，一条命令启动

---

## 4. 系统架构

```
┌─────────────────────────────────────────────────────┐
│  Frontend (Vue 3, port 5173)                         │
│  ┌──────────────────────────────────────────────┐   │
│  │ 识别页（上传态 → 结果态，同路由状态切换）        │   │
│  ├──────────────────────────────────────────────┤   │
│  │ 历史记录页（独立路由）                          │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP REST (JSON)
┌─────────────────────▼───────────────────────────────┐
│  Backend (FastAPI, port 8000)                        │
│                                                     │
│  POST /api/recognize        全图识别                  │
│  POST /api/recognize/roi    ROI 区域识别              │
│  GET  /api/records          历史记录列表（分页+筛选）  │
│  GET  /api/records/{id}     单条记录详情              │
│  GET  /api/records/export   CSV 导出                 │
│  GET  /api/images/{file}    原图静态资源              │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ RecognizeService                             │   │
│  │  1. HyperLPR3 初次识别                       │   │
│  │  2. 检查所有车牌 confidence ≥ 0.9？           │   │
│  │     否 → Real-ESRGAN 对低置信度区域超分        │   │
│  │         → 重新识别该区域                      │   │
│  │         → 合并结果，标记 used_sr=true         │   │
│  │  3. 写入 SQLite，返回结果                      │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  SQLite: records 表 + images/ 目录                   │
└─────────────────────────────────────────────────────┘
```

---

## 5. 数据模型

### records 表

```sql
CREATE TABLE records (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_path  TEXT NOT NULL,      -- 相对于 images/ 目录的文件名
    plates      TEXT NOT NULL,      -- JSON 字符串，见下方结构
    used_sr     INTEGER DEFAULT 0   -- 0=未触发超分, 1=已触发
);
```

### plates JSON 结构（每条记录）

```json
[
  {
    "text": "粤B88888",
    "province": "粤",
    "city_code": "B",
    "number": "88888",
    "type": "blue",
    "type_label": "普通蓝牌",
    "confidence": 0.91,
    "confidence_before_sr": 0.78,
    "bbox": [x, y, width, height]
  }
]
```

### 车牌类型枚举

| type 值 | 说明 | 渲染颜色 |
|---------|------|---------|
| `blue` | 普通蓝牌（小型民用）| 蓝底白字 |
| `green_small` | 新能源小型 | 绿→黄绿渐变底黑字 |
| `yellow` | 黄牌（大型/货车/教练）| 黄底黑字 |
| `white` | 警牌/武警/军牌 | 白底黑字 |
| `black` | 使馆/港澳 | 黑底白字 |

---

## 6. API 规范

### POST /api/recognize
```
Content-Type: multipart/form-data
Body: image (file)

Response 200:
{
  "record_id": 42,
  "plates": [...],       // plates JSON 结构
  "used_sr": false,
  "duration_ms": 320,
  "multi_vehicle": false // 是否检测到多辆车
}
```

### POST /api/recognize/roi
```
Content-Type: multipart/form-data
Body: image (file), roi_x, roi_y, roi_w, roi_h (int)

Response 200: 同上
```

### GET /api/records
```
Query: page=1, limit=20, plate=, type=, date_from=, date_to=

Response 200:
{
  "total": 42,
  "items": [{ "id", "created_at", "plates", "used_sr", "image_url" }]
}
```

### GET /api/records/export
```
Query: format=csv (目前仅支持 csv)
Response: 文件流下载，Content-Disposition: attachment; filename=records.csv
```

---

## 7. 前端页面设计

### 7.1 识别页

**上传态**
- 拖拽 / 点击上传区域
- ROI 框选区域：默认隐藏，仅当后端返回 `multi_vehicle: true` 时展示
  - 展示原图，用户拖拽绘制矩形框选目标车辆
  - 提供"跳过"按钮，跳过后识别全图
- 操作按钮：「重置」「开始识别」，等宽 140px

**结果态（同路由，状态切换）**
- 左侧：原始图片 + 车牌位置框覆盖层（绿色边框标注）
- 右侧：每张车牌一个卡片
  - 以真实车牌配色渲染车牌号（见车牌类型枚举）
  - 置信度进度条
  - 若 `used_sr: true`，显示橙色提示"已自动启用超分增强"及超分前置信度
  - 耗时 + 时间戳
- 操作按钮：「重新识别」「保存记录」，等宽 140px

### 7.2 历史记录页

- 筛选栏：车牌号搜索框 + 类型下拉 + 时间范围下拉 + 导出 CSV 按钮
- 表格列：缩略图 | 车牌（带颜色渲染）| 置信度 | 超分 | 识别时间 | 操作
- 分页：每页 20 条

### 7.3 全局底部免责声明

所有页面底部固定显示灰底小字：

> 免责声明　本工具仅提供车牌图像识别辅助功能，识别结果由 AI 模型自动生成，可能存在误识别或遗漏，不构成任何法律证明或执法依据。用户在将识别结果用于违章举报或其他用途前，须自行核实原始图像信息，并承担相应责任。本平台不存储用户上传的图片，不对识别结果的准确性作出保证。

---

## 8. 识别流程（详细）

```
用户上传图片
  │
  ▼
后端接收图片 → 保存到 images/ 目录（UUID 文件名）
  │
  ▼
HyperLPR3 全图/ROI 识别 → 返回 [{text, bbox, confidence, type}]
  │
  ├── multi_vehicle 判断：检测到 bbox 数量 > 1？
  │     是 → response 中 multi_vehicle=true，前端展示 ROI 框选
  │     否 → 继续
  │
  ▼
遍历所有识别结果
  对每个 confidence < 0.9 的车牌：
    → 按 bbox 裁剪车牌区域
    → Real-ESRGAN 超分（4× 放大）
    → HyperLPR3 重新识别裁剪区域
    → 更新 confidence，记录 confidence_before_sr
    → used_sr = true
  │
  ▼
写入 SQLite records 表
  │
  ▼
返回 JSON 结果
```

---

## 9. 错误处理

| 场景 | 处理方式 |
|------|---------|
| 文件格式不支持 | 前端上传前校验，提示"仅支持 JPG/PNG/BMP" |
| 文件过大 | 前端上传前校验，提示"文件不超过 20MB" |
| 未检测到车牌 | 返回空 plates 数组，前端展示"未检测到车牌，请尝试更换图片或框选目标区域" |
| 超分超时（> 30s）| 取消超分，返回原始识别结果，置信度标注为"未增强" |
| 后端服务不可达 | 前端 API 调用统一 error handler，toast 提示"服务异常，请稍后重试" |

---

## 10. 目录结构（预期）

```
licensePlateRecognition/
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── RecognizePage.vue
│   │   │   └── HistoryPage.vue
│   │   ├── components/
│   │   │   ├── UploadZone.vue
│   │   │   ├── RoiSelector.vue
│   │   │   ├── PlateCard.vue
│   │   │   ├── PlateVisual.vue      # 车牌颜色渲染组件
│   │   │   └── HistoryTable.vue
│   │   ├── api/
│   │   │   └── index.ts
│   │   └── router/
│   │       └── index.ts
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── main.py                      # FastAPI app 入口
│   ├── recognize.py                 # RecognizeService
│   ├── database.py                  # SQLite 操作
│   ├── models.py                    # Pydantic 数据模型
│   ├── config.py                    # 配置（置信度阈值等）
│   ├── images/                      # 用户上传图片存储
│   ├── lpr.db                       # SQLite 数据库文件
│   └── requirements.txt
│
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-03-30-license-plate-recognition-design.md
```

---

## 11. 后续迭代（范围外，记录备用）

- 完整违章举报流程：地点信息（GPS/手动输入）、违章类型标注、举报记录管理
- 视频文件支持：逐帧抽取后批量识别
- 大型新能源黄绿渐变牌支持
- Docker Compose 生产部署配置
