# shared

Small provider helpers for getting a chat model or embedding model without repeating
initialisation across notebooks.

```python
from shared import get_llm, get_embeddings
llm = get_llm()                 # provider default
llm = get_llm("openai")         # or "groq", "databricks"
```

Supported: OpenAI, Groq, Databricks (`ChatDatabricks` / `DatabricksEmbeddings`), plus a
Databricks AI Gateway variant. Keys come from `.env` — see `.env.example`.

> **Nothing in this repo currently imports this package.** Every notebook initialises its
> own model inline, which keeps each one copy-pasteable. It is kept because it is the
> obvious place to centralise provider switching if that changes.
