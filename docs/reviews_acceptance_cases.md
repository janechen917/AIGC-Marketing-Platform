# 批量好评模块验收样例（L2）

目的：固定可复测输入与验收标准，覆盖参数边界、去重质量与 CSV 导出体验。

## 样例 1：标准批量生成（20 条）

输入（POST /api/reviews/generate）：

```json
{
  "product_name": "品牌A咖啡液",
  "selling_points": ["低糖", "冷萃香气", "便携即饮"],
  "platform": "小红书",
  "style": "真实口碑",
  "target_count": 20,
  "batch_size": 8,
  "max_rounds": 10,
  "similarity_threshold": 0.85,
  "persona_pool": ["宝妈", "学生", "上班族"]
}
```

验收检查：
- HTTP 状态为 200
- 返回字段包含 reviews、total_generated、rounds、deduped_dropped、compliance_dropped、csv_content
- csv_content 头部为 index,review

## 样例 2：高密度去重场景（30 条）

输入（POST /api/reviews/generate）：

```json
{
  "product_name": "品牌B防晒喷雾",
  "selling_points": ["清爽不黏", "快速成膜"],
  "platform": "微博",
  "style": "种草",
  "target_count": 30,
  "batch_size": 10,
  "max_rounds": 15,
  "similarity_threshold": 0.8,
  "persona_pool": ["学生", "户外爱好者", "上班族"]
}
```

验收检查：
- total_generated <= target_count
- deduped_dropped >= 0，且结果列表无明显重复
- rounds <= max_rounds

## 样例 3：边界规模场景（100 条）

输入（POST /api/reviews/generate）：

```json
{
  "product_name": "品牌C空气炸锅",
  "selling_points": ["大容量", "少油健康", "多菜单"],
  "platform": "抖音",
  "style": "理性专业",
  "target_count": 100,
  "batch_size": 20,
  "max_rounds": 5,
  "similarity_threshold": 0.95,
  "persona_pool": ["家庭用户", "健身人群", "上班族"],
  "require_hashtag": false,
  "require_cta": false
}
```

验收检查：
- HTTP 状态为 200
- 在 max_rounds 内完成目标条数或达到可解释上限
- CSV 下载文件名可用、内容可被表格工具直接读取

## 建议执行

```bash
cd backend
uv run pytest -q tests/test_reviews.py tests/test_review_generator.py
```
