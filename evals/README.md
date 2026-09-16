# Retrieval evaluation dataset

Create a JSONL file with one labelled case per line. Prefer stable `gold_chunk_ids` after a full knowledge-base build; `gold_sources` is supported for document-level evaluation.

```json
{"id":"setting-001","query":"示例设备的过流保护定值是多少？","gold_chunk_ids":["ck-replace-with-real-id"]}
{"id":"procedure-001","query":"示例故障应执行哪些检查？","gold_sources":["replace-with-real-document.pdf"]}
```

Run:

```powershell
python scripts/evaluate_retrieval.py --dataset evals/retrieval_cases.jsonl --strategy hybrid --k 10 --output data/eval/latest.json
```

Run the same dataset with `--strategy dense`, `sparse`, `graph` and `hybrid` for a controlled ablation. The repository does not include fabricated benchmark scores. Add labels from documents you are authorized to use before publishing metrics.
