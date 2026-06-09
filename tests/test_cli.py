from docintel.cli import print_benchmark_summary


def test_print_benchmark_summary_renders_table() -> None:
    summary = [
        {
            "tier": "Text fixtures",
            "documents": 8,
            "extractor": "text",
            "llm": "ollama",
            "model": "qwen2.5:0.5b",
            "overall": 1.0,
            "predictions": "outputs/qwen2_5_0_5b_text_predictions.json",
        }
    ]

    print_benchmark_summary(summary)