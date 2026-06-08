from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from docintel.extractors import build_extractor  # noqa: E402
from docintel.llm import build_llm  # noqa: E402
from docintel.pipeline import DocumentIntelligencePipeline  # noqa: E402

st.set_page_config(page_title="Local Document Intelligence", page_icon="📄", layout="wide")

st.title("Local Document Intelligence")

extractor_name = st.sidebar.selectbox("Extractor", ["text", "rapidocr", "paddleocr"])
llm_name = st.sidebar.selectbox("LLM", ["heuristic", "ollama"])
model_name = st.sidebar.text_input("Ollama model", "qwen2.5:1.5b")
max_retries = st.sidebar.number_input("Repair attempts", min_value=0, max_value=5, value=2)

uploaded = st.file_uploader(
    "Upload a document image or text fixture",
    type=["txt", "png", "jpg", "jpeg"],
)

if uploaded:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(uploaded.getbuffer())
        temp_path = Path(handle.name)

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Input")
        if suffix.lower() == ".txt":
            st.text(temp_path.read_text(encoding="utf-8"))
        else:
            st.image(str(temp_path), use_container_width=True)

    if st.button("Extract JSON", type="primary"):
        try:
            pipeline = DocumentIntelligencePipeline(
                extractor=build_extractor(extractor_name),
                llm=build_llm(llm_name, model=model_name),
                max_retries=int(max_retries),
            )
            result = pipeline.run(temp_path)
            with right:
                st.subheader("Validated JSON")
                st.json(result.document.model_dump(mode="json"))
                st.caption(f"Validated after {result.attempts} attempt(s)")
                with st.expander("Raw extracted text"):
                    st.text(result.extraction.full_text)
                with st.expander("Raw model response"):
                    st.code(result.raw_response, language="json")
                st.download_button(
                    "Download JSON",
                    data=json.dumps(result.document.model_dump(mode="json"), indent=2),
                    file_name="extracted_document.json",
                    mime="application/json",
                )
        except Exception as exc:
            st.error(str(exc))
