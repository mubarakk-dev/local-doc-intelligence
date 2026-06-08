# Project Structure

```text
src/docintel/
  extractors/      Local document text/layout extraction backends.
  llm/             Local model clients and prompts.
  schemas.py       Strict UK invoice/receipt output contract.
  validation.py    JSON parsing and Pydantic validation helpers.
  pipeline.py      End-to-end extraction orchestration.
  evaluation.py    Field-level benchmark scoring.
  cli.py           Command-line interface.
app/
  streamlit_app.py Local demo UI.
data/
  samples/         Safe sample fixtures.
  ground_truth.json Benchmark labels.
docs/
  failure_analysis.md
  portfolio_notes.md
```

The code intentionally separates extraction, reasoning, validation, and evaluation so each
layer can be tested or replaced independently.

