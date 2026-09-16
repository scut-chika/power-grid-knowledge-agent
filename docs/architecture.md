# 系统架构

## 1. 设计目标

系统面向电网二次运维文档检索与知识问答，优先保证三件事：

1. 每条回答能够追溯到文件、页码或章节；
2. 语义、关键词和图谱检索互相补充，而不是串行兜底；
3. 在没有外部模型或 Neo4j 的本地环境中，系统仍能以降级模式运行并明确标记能力边界。

## 2. 模块划分

```text
src/knowledge_base
  ├─ data_loader       原始文件扫描与文件名元数据
  ├─ preprocess        多格式解析、结构化单元与重叠分块
  ├─ vector_store      zvec 稠密向量索引
  ├─ sparse_store      本地持久化 BM25 索引
  ├─ knowledge_extraction  可审计的规则实体/关系抽取基线
  ├─ graph_builder     Neo4j 写入与参数化 Cypher 查询
  └─ pipeline.py       三类索引的一致性构建

src/rag_engine
  ├─ vector_retriever.py
  ├─ sparse_retriever.py
  ├─ graph_retriever.py
  ├─ fusion.py         Reciprocal Rank Fusion
  ├─ reranker.py       可选外部精排
  └─ context_assembler.py

src/agent
  ├─ intent_recognition.py
  ├─ task_planner.py
  ├─ tool_calling.py
  └─ skills/           文档解析、条款比对、风险检查与报告生成
```

## 3. 入库链路

1. 扫描 `data/raw` 下支持的文件；
2. 计算文件路径、大小和修改时间指纹；
3. PDF 按页、DOCX 按标题/表格、文本按章节、表格按行区间解析；
4. 在结构化单元内部进行带重叠的分块；
5. 为 Chunk 附加 `document_id`、`chunk_id`、页码、章节、行范围等元数据；
6. 同一次构建中同步更新 zvec、BM25 和 Neo4j，避免多索引版本不一致；
7. 保存构建状态；语料未变化时跳过重复索引。

当前数据量定位为单机原型，因此语料发生变化时采用完整重建策略，以一致性换取实现复杂度。若未来达到大规模生产数据量，再引入版本化增量索引与任务队列。

## 4. 查询链路

```text
用户问题
  → 规范化、意图与实体识别
  → Dense / Sparse / Graph 线程池并发召回与通道故障隔离
  → 基于 chunk_id 的去重
  → RRF 融合不同分数空间下的排名
  → 可选 Reranker API 精排
  → 组装带来源位置的上下文
  → LLM 或本地降级答案
```

RRF 分数被归一化至 `[0, 1]`。配置精排模型后，最终得分由精排相关性与融合分数共同组成；未配置时保留 RRF 排名，不生成虚假的模型相关性分数。

查询响应的 `retrieval.latency_ms` 记录 Dense、Sparse、Graph、融合、精排、上下文组装和总时延；单路召回异常记录在 `retrieval.errors`，不会阻断其他召回通道。

## 5. 图谱边界

当前图谱抽取是确定性规则基线：识别厂站、线路、母线、装置、断路器、定值项与文档等实体，构建 `CONTAINS` 和 `MENTIONS` 关系。图谱检索返回命中实体的一跳邻域。

这套实现适合演示可追踪的数据闭环，但不等同于 LLM 信息抽取或复杂多跳推理。后续可在保持同一实体结构的前提下增加：

- Pydantic 结构化的 LLM 实体关系抽取；
- 实体别名归一化与人工审核；
- 设备—保护—定值等领域本体；
- 有明确问题模板约束的 1～2 跳 Cypher 检索。

## 6. 评测

`scripts/evaluate_retrieval.py` 读取人工标注 JSONL，计算 Recall@K、HitRate@K 和 MRR。建议至少比较以下配置：

1. Dense only；
2. Sparse only；
3. Dense + Sparse；
4. Dense + Sparse + Graph；
5. Hybrid + Reranker。

仓库不提供虚构分数。只有在固定语料、固定问题集上运行得到的结果，才可以用于报告或简历量化。

## 7. 后续演进顺序

1. 用真实授权文档建立评测集；
2. 改进领域实体标准化与图谱关系；
3. 增加 LLM 结构化抽取及人工审核；
4. 数据规模扩大后引入 Redis/Celery 和版本化索引；
5. 业务确实需要可恢复状态和人工审批时，再迁移至 LangGraph。
