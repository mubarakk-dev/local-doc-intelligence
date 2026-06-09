from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from docintel.evaluation import evaluate_files
from docintel.extractors import build_extractor
from docintel.llm import build_llm
from docintel.pipeline import DocumentIntelligencePipeline
from docintel.synthetic import generate_synthetic_dataset

app = typer.Typer(help="Local document intelligence for UK invoices and receipts.")
console = Console()


@app.command()
def extract(
    path: Path = typer.Argument(
        ...,
        exists=True,
        help="Document image, PDF page, or text fixture.",
    ),
    extractor: str = typer.Option("text", help="Extractor backend: text, paddleocr, donut."),
    llm: str = typer.Option("heuristic", help="LLM backend: heuristic, ollama."),
    model: str | None = typer.Option(None, help="Local model name, e.g. qwen2.5:1.5b."),
    output: Path = typer.Option(Path("outputs/predictions.json"), help="Prediction JSON path."),
    max_retries: int = typer.Option(2, help="Validation repair attempts."),
) -> None:
    pipeline = DocumentIntelligencePipeline(
        extractor=build_extractor(extractor),
        llm=build_llm(llm, model=model),
        max_retries=max_retries,
    )
    result = pipeline.run(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    prediction_record = {
        "file": str(path).replace("\\", "/"),
        "prediction": result.document.model_dump(mode="json"),
        "metadata": {
            "extractor": result.extraction.extractor_name,
            "llm": llm,
            "attempts": result.attempts,
        },
    }
    output.write_text(json.dumps([prediction_record], indent=2), encoding="utf-8")
    console.print_json(data=prediction_record)
    console.print(f"\nSaved prediction to [bold]{output}[/bold]")


@app.command()
def batch(
    input_dir: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        help="Directory of documents.",
    ),
    pattern: str = typer.Option("*.txt", help="Glob pattern, e.g. *.txt or *.png."),
    extractor: str = typer.Option("text", help="Extractor backend: text, paddleocr, donut."),
    llm: str = typer.Option("heuristic", help="LLM backend: heuristic, ollama."),
    model: str | None = typer.Option(None, help="Local model name, e.g. qwen2.5:0.5b."),
    output: Path = typer.Option(Path("outputs/predictions.json"), help="Prediction JSON path."),
    max_retries: int = typer.Option(2, help="Validation repair attempts."),
) -> None:
    pipeline = DocumentIntelligencePipeline(
        extractor=build_extractor(extractor),
        llm=build_llm(llm, model=model),
        max_retries=max_retries,
    )
    records = []
    paths = sorted(input_dir.glob(pattern))
    if not paths:
        raise typer.BadParameter(f"No files matched {input_dir / pattern}")

    for path in paths:
        result = pipeline.run(path)
        records.append(
            {
                "file": str(path).replace("\\", "/"),
                "prediction": result.document.model_dump(mode="json"),
                "metadata": {
                    "extractor": result.extraction.extractor_name,
                    "llm": llm,
                    "attempts": result.attempts,
                },
            }
        )
        console.print(f"[green]OK[/green] {path}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, indent=2), encoding="utf-8")
    console.print(f"\nSaved {len(records)} predictions to [bold]{output}[/bold]")


@app.command()
def evaluate(
    ground_truth: Path = typer.Argument(
        ...,
        exists=True,
        help="Ground-truth JSON file.",
    ),
    predictions: Path = typer.Option(Path("outputs/predictions.json"), exists=True),
) -> None:
    report = evaluate_files(ground_truth, predictions)
    table = Table(title="Extraction Accuracy")
    table.add_column("Field")
    table.add_column("Score", justify="right")
    for metric in report.field_scores:
        table.add_row(metric.field, f"{metric.score:.2f}")
    table.add_section()
    table.add_row("overall", f"{report.overall:.2f}")
    console.print(table)


@app.command("generate-samples")
def generate_samples(
    samples_dir: Path = typer.Option(
        Path("data/samples"),
        help="Output directory for text fixtures.",
    ),
    ground_truth: Path = typer.Option(
        Path("data/ground_truth.json"),
        help="Ground-truth JSON path.",
    ),
    image_dir: Path = typer.Option(
        Path("data/sample_images"),
        help="Output directory for PNG previews.",
    ),
    include_degraded: bool = typer.Option(
        False,
        help="Also generate degraded PNG previews for OCR stress testing.",
    ),
    degraded_image_dir: Path = typer.Option(
        Path("data/sample_images_degraded"),
        help="Output directory for degraded PNG previews.",
    ),
) -> None:
    records = generate_synthetic_dataset(
        samples_dir=samples_dir,
        ground_truth_path=ground_truth,
        image_dir=image_dir,
        degraded_image_dir=degraded_image_dir if include_degraded else None,
    )
    console.print(f"Generated [bold]{len(records)}[/bold] synthetic documents.")
    console.print(f"Text fixtures: [bold]{samples_dir}[/bold]")
    console.print(f"Image previews: [bold]{image_dir}[/bold]")
    if include_degraded:
        console.print(f"Degraded image previews: [bold]{degraded_image_dir}[/bold]")
    console.print(f"Ground truth: [bold]{ground_truth}[/bold]")


if __name__ == "__main__":
    app()
