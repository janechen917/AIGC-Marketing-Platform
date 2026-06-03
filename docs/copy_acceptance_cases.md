# 文案模块验收样例（L1）

目的：固定可复测的输入与验收口径，用于本地回归与后续模型调整对比。

## 样例 1：小红书轻营销（均衡）

输入（POST /api/copy/generate）：

```json
{
  "product_name": "品牌A咖啡液",
  "selling_points": ["低糖", "冷萃香气", "便携即饮"],
  "target_audience": "通勤上班族",
  "platform": "小红书",
  "style": "专业",
  "length_hint": "中等",
  "title_count": 3,
  "brand_name": "品牌A"
}
```

验收检查：
- HTTP 状态为 200
- 返回包含 draft_text、polished_text、draft_model、polish_model、compliance
- compliance 包含 passed、issue_count、issues

## 样例 2：微博短促风格（简洁）

输入（POST /api/copy/generate）：

```json
{
  "product_name": "品牌B防晒喷雾",
  "selling_points": ["清爽不黏", "快速成膜"],
  "target_audience": "户外通勤人群",
  "platform": "微博",
  "style": "活泼",
  "length_hint": "短",
  "title_count": 2,
  "brand_name": "品牌B",
  "require_hashtag": true,
  "require_cta": true
}
```

验收检查：
- HTTP 状态为 200
- draft_model 与 polish_model 为非空字符串
- compliance.issues 为数组

## 样例 3：公众号长文导向（信息型）

输入（POST /api/copy/generate）：

```json
{
  "product_name": "品牌C空气炸锅",
  "selling_points": ["大容量", "少油健康", "多菜单"],
  "target_audience": "家庭用户",
  "platform": "公众号",
  "style": "专业",
  "length_hint": "长",
  "title_count": 4,
  "brand_name": "品牌C",
  "max_length": 1200,
  "max_emojis": 3
}
```

验收检查：
- HTTP 状态为 200
- polished_text 为非空字符串
- compliance 字段结构完整

## 建议执行

后端快速验证：

```bash
cd backend
uv run pytest -q tests/test_copywriter.py
```
