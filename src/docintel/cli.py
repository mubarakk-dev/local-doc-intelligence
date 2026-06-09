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
    extractor: str = typer.Option(
        "text",
        help="Extractor backend: text, rapidocr, paddleocr, donut.",
    ),
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
    extractor: str = typer.Option(
        "text",
        help="Extractor backend: text, rapidocr, paddleocr, donut.",
    ),
    llm: str = typer.Option("heuristic", help="LLM backend: heuristic, ollama."),
    model: str | None = typer.Option(None, help="Local model name, e.g. qwen2.5:0.5b."),
    output: Path = typer.Option(Path("outputs/predictions.json"), help="Prediction JSON path."),
    max_retries: int = typer.Option(2, help="Validation repair attempts."),
) -> None:
    records = run_batch_extraction(
        input_dir=input_dir,
        pattern=pattern,
        extractor=extractor,
        llm=llm,
        model=model,
        output=output,
        max_retries=max_retries,
    )
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


@app.command()
def benchmark(
    llm: str = typer.Option("ollama", help="LLM backend: heuristic, ollama."),
    model: str = typer.Option("qwen2.5:0.5b", help="Local model name."),
    output_dir: Path = typer.Option(Path("outputs"), help="Directory for prediction files."),
    max_retries: int = typer.Option(2, help="Validation repair attempts."),
) -> None:
    generate_synthetic_dataset(
        samples_dir=Path("data/samples"),
        ground_truth_path=Path("data/ground_truth.json"),
        image_dir=Path("data/sample_images"),
        degraded_image_dir=Path("data/sample_images_degraded"),
        photo_image_dir=Path("data/sample_images_photo"),
    )

    safe_model = model.replace(":", "_").replace(".", "_")
    tiers = [
        {
            "name": "Text fixtures",
            "input_dir": Path("data/samples"),
            "pattern": "*.txt",
            "extractor": "text",
            "output": output_dir / f"{safe_model}_text_predictions.json",
        },
        {
            "name": "Clean generated PNGs",
            "input_dir": Path("data/sample_images"),
            "pattern": "*.png",
            "extractor": "rapidocr",
            "output": output_dir / f"{safe_model}_clean_ocr_predictions.json",
        },
        {
            "name": "Degraded synthetic PNGs",
            "input_dir": Path("data/sample_images_degraded"),
            "pattern": "*.png",
            "extractor": "rapidocr",
            "output": output_dir / f"{safe_model}_degraded_ocr_predictions.json",
        },
        {
            "name": "Photo-style synthetic PNGs",
            "input_dir": Path("data/sample_images_photo"),
            "pattern": "*.png",
            "extractor": "rapidocr",
            "output": output_dir / f"{safe_model}_photo_ocr_predictions.json",
        },
    ]

    summary = []
    for tier in tiers:
        records = run_batch_extraction(
            input_dir=tier["input_dir"],
            pattern=str(tier["pattern"]),
            extractor=str(tier["extractor"]),
            llm=llm,
            model=model,
            output=tier["output"],
            max_retries=max_retries,
            verbose=False,
        )
        report = evaluate_files(Path("data/ground_truth.json"), tier["output"])
        summary.append(
            {
                "tier": tier["name"],
                "documents": len(records),
                "extractor": tier["extractor"],
                "llm": llm,
                "model": model,
                "overall": report.overall,
                "predictions": str(tier["output"]).replace("\\", "/"),
            }
        )

    summary_path = output_dir / "benchmark_summary.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print_benchmark_summary(summary)
    console.print(f"\nSaved benchmark summary to [bold]{summary_path}[/bold]")


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
    include_photo_style: bool = typer.Option(
        False,
        help="Also generate photo-style PNG previews for OCR stress testing.",
    ),
    photo_image_dir: Path = typer.Option(
        Path("data/sample_images_photo"),
        help="Output directory for photo-style PNG previews.",
    ),
) -> None:
    records = generate_synthetic_dataset(
        samples_dir=samples_dir,
        ground_truth_path=ground_truth,
        image_dir=image_dir,
        degraded_image_dir=degraded_image_dir if include_degraded else None,
        photo_image_dir=photo_image_dir if include_photo_style else None,
    )
    console.print(f"Generated [bold]{len(records)}[/bold] synthetic documents.")
    console.print(f"Text fixtures: [bold]{samples_dir}[/bold]")
    console.print(f"Image previews: [bold]{image_dir}[/bold]")
    if include_degraded:
        console.print(f"Degraded image previews: [bold]{degraded_image_dir}[/bold]")
    if include_photo_style:
        console.print(f"Photo-style image previews: [bold]{photo_image_dir}[/bold]")
    console.print(f"Ground truth: [bold]{ground_truth}[/bold]")


def run_batch_extraction(
    input_dir: Path,
    pattern: str,
    extractor: str,
    llm: str,
    model: str | None,
    output: Path,
    max_retries: int,
    verbose: bool = True,
) -> list[dict[str, object]]:
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
        if verbose:
            console.print(f"[green]OK[/green] {path}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


def print_benchmark_summary(summary: list[dict[str, object]]) -> None:
    table = Table(title="Benchmark Results")
    table.add_column("Tier")
    table.add_column("Extractor")
    table.add_column("LLM")
    table.add_column("Documents", justify="right")
    table.add_column("Overall", justify="right")
    for row in summary:
        table.add_row(
            str(row["tier"]),
            str(row["extractor"]),
            f"{row['llm']}/{row['model']}",
            str(row["documents"]),
            f"{float(row['overall']):.2f}",
        )
    console.print(table)


if __name__ == "__main__":
    app()