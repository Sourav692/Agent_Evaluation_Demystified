# LLM as Judge

A minimal DeepEval G-Eval correctness judge — criteria plus an `LLMTestCase`, nothing else.
The smallest possible example of judging output with a model instead of a rule.

| Path | Content |
|---|---|
| `DeepEval_GEval/test_firstdeepeval.py` | Minimal G-Eval correctness judge |

```bash
deepeval test run labs/llm-as-judge/DeepEval_GEval/test_firstdeepeval.py
```

Needs `OPENAI_API_KEY`.

**For more depth:**
- RAG-specific G-Eval rubrics — [`../rag-evaluation/3.Custom_LLM_as_a_Judge_(G-Eval).ipynb`](../rag-evaluation/3.Custom_LLM_as_a_Judge_%28G-Eval%29.ipynb)
- What LLM-as-judge gets wrong, and how to align a judge to human labels — course 02
  phase 7 ([`../../courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb`](../../courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb))
