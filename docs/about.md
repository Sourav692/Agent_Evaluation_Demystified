# About

Maintained by **Sourav Banerjee**.
Sourav wrote the repository's three courses: RAG, agent and tool evaluation across DeepEval,
RAGAS, MLflow and Phoenix; MLflow 3 GenAI evaluation on Databricks, from tracing to judge
alignment; and an agentic evaluation harness that ends in a release gate wired to CI.

This site is the written half of a hands-on course in evaluating RAG systems and agents.
The runnable half is the notebooks in the
[GitHub repository](https://github.com/Sourav692/Agent_Evaluation_Demystified): three
courses and a set of labs.

## Report a problem

Open an issue on GitHub:
[report an issue](https://github.com/Sourav692/Agent_Evaluation_Demystified/issues/new).
A wrong number, a broken link and an unclear explanation are all worth one. Name the page
and the section.

## How the site is built

Every page here is a Markdown or HTML file under `docs/` in the repository. The Markdown is
canonical. `site/build.py` renders it into static HTML. A push to `main` rebuilds and
deploys the site on Vercel, so every live version matches a commit. What changed and when
is in the [changelog](CHANGELOG.md).

## Privacy

The site sets no cookies and has no accounts. Page views are counted with cookieless
analytics. The drill's recall ratings and any reading progress stay in your browser's own
storage and never reach a server.

## Licences and credits

Code is under the [MIT licence](../LICENSE). Written material — the pages here and the
notebooks' prose — is under [CC BY 4.0](../LICENSE-docs): reuse it with credit.
Third-party folders keep their own terms, listed in [THIRD_PARTY.md](../THIRD_PARTY.md).
