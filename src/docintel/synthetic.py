from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


@dataclass(frozen=True)
class SyntheticDocument:
    file_stem: str
    text: str
    expected: dict[str, object]


SYNTHETIC_DOCUMENTS = [
    SyntheticDocument(
        file_stem="invoice_001",
        text="""INVOICE

Acme Services Ltd
10 Example Street
London
EC1A 1AA

VAT Number: GB123456789
Invoice Number: INV-2026-001
Invoice Date: 31 January 2026

Bill To:
Northbank Coffee Ltd
22 Market Road
London

Subtotal: \u00a3100.00
VAT: \u00a320.00
Total: \u00a3120.00
""",
        expected={
            "document_type": "invoice",
            "supplier_name": "Acme Services Ltd",
            "supplier_address": "10 Example Street, London, EC1A 1AA",
            "vat_number": "GB123456789",
            "invoice_number": "INV-2026-001",
            "invoice_date": "2026-01-31",
            "subtotal_gbp": 100.0,
            "vat_amount_gbp": 20.0,
            "total_amount_gbp": 120.0,
            "currency": "GBP",
            "confidence": 0.8,
        },
    ),
    SyntheticDocument(
        file_stem="invoice_002_commas",
        text="""TAX INVOICE

Thames Analytics Limited
81 Borough High Street
London
SE1 1DN

Invoice No: TA-4588
Invoice Date: 03/02/2026
VAT Number: 987654321

Subtotal: GBP 1,250.00
VAT: GBP 250.00
Total: GBP 1,500.00
""",
        expected={
            "document_type": "invoice",
            "supplier_name": "Thames Analytics Limited",
            "supplier_address": "81 Borough High Street, London, SE1 1DN",
            "vat_number": "GB987654321",
            "invoice_number": "TA-4588",
            "invoice_date": "2026-02-03",
            "subtotal_gbp": 1250.0,
            "vat_amount_gbp": 250.0,
            "total_amount_gbp": 1500.0,
            "currency": "GBP",
            "confidence": 0.8,
        },
    ),
    SyntheticDocument(
        file_stem="invoice_003_no_vat",
        text="""INVOICE

Brighton Legal Support
14 Temple Avenue
London
EC4Y 0DA

Invoice #: BLS-2026-044
Date: 12 March 2026

Professional services: \u00a3450.00
Total: \u00a3450.00
""",
        expected={
            "document_type": "invoice",
            "supplier_name": "Brighton Legal Support",
            "supplier_address": "14 Temple Avenue, London, EC4Y 0DA",
            "vat_number": None,
            "invoice_number": "BLS-2026-044",
            "invoice_date": "2026-03-12",
            "subtotal_gbp": None,
            "vat_amount_gbp": None,
            "total_amount_gbp": 450.0,
            "currency": "GBP",
            "confidence": 0.8,
        },
    ),
    SyntheticDocument(
        file_stem="receipt_001_cafe",
        text="""RECEIPT

Northbank Coffee Ltd
22 Market Road
London
N1 6AB

Receipt No: RCPT-8821
Date: 05 April 2026

Flat white \u00a33.40
Croissant \u00a32.60
Total: \u00a36.00
""",
        expected={
            "document_type": "receipt",
            "supplier_name": "Northbank Coffee Ltd",
            "supplier_address": "22 Market Road, London, N1 6AB",
            "vat_number": None,
            "invoice_number": "RCPT-8821",
            "invoice_date": "2026-04-05",
            "subtotal_gbp": None,
            "vat_amount_gbp": None,
            "total_amount_gbp": 6.0,
            "currency": "GBP",
            "confidence": 0.8,
        },
    ),
    SyntheticDocument(
        file_stem="receipt_002_vat",
        text="""VAT RECEIPT

City Office Supplies
4 Clerkenwell Road
London
EC1M 5PQ

VAT Number: GB222333444
Receipt Number: COS-772
Date: 18/04/2026

Subtotal: \u00a342.50
VAT: \u00a38.50
Total: \u00a351.00
""",
        expected={
            "document_type": "receipt",
            "supplier_name": "City Office Supplies",
            "supplier_address": "4 Clerkenwell Road, London, EC1M 5PQ",
            "vat_number": "GB222333444",
            "invoice_number": "COS-772",
            "invoice_date": "2026-04-18",
            "subtotal_gbp": 42.5,
            "vat_amount_gbp": 8.5,
            "total_amount_gbp": 51.0,
            "currency": "GBP",
            "confidence": 0.8,
        },
    ),
    SyntheticDocument(
        file_stem="invoice_004_bill_to_first",
        text="""INVOICE

Bill To:
Camden Retail Group
7 High Road
London

Supplier:
Ledger Lane Bookkeeping
9 Fleet Street
London
EC4Y 1AA

VAT Number: GB555666777
Invoice Number: LLB-9001
Invoice Date: 2026-05-02

Subtotal: \u00a3700.00
VAT: \u00a3140.00
Total: \u00a3840.00
""",
        expected={
            "document_type": "invoice",
            "supplier_name": "Ledger Lane Bookkeeping",
            "supplier_address": "9 Fleet Street, London, EC4Y 1AA",
            "vat_number": "GB555666777",
            "invoice_number": "LLB-9001",
            "invoice_date": "2026-05-02",
            "subtotal_gbp": 700.0,
            "vat_amount_gbp": 140.0,
            "total_amount_gbp": 840.0,
            "currency": "GBP",
            "confidence": 0.8,
        },
    ),
    SyntheticDocument(
        file_stem="invoice_005_noisy_ocr",
        text="""INVOICE

West End Catering Co
55 0xford Street
L0ndon
W1D 2LT

VAT Numher: GB333444555
Invoice Number: WEC-118
Invoice Date: 27 May 2026

SubtotaI: \u00a3300.00
VAT: \u00a360.00
TotaI: \u00a3360.00
""",
        expected={
            "document_type": "invoice",
            "supplier_name": "West End Catering Co",
            "supplier_address": "55 0xford Street, L0ndon, W1D 2LT",
            "vat_number": "GB333444555",
            "invoice_number": "WEC-118",
            "invoice_date": "2026-05-27",
            "subtotal_gbp": 300.0,
            "vat_amount_gbp": 60.0,
            "total_amount_gbp": 360.0,
            "currency": "GBP",
            "confidence": 0.8,
        },
    ),
    SyntheticDocument(
        file_stem="invoice_006_reverse_charges",
        text="""INVOICE

Canary Wharf Data Services
1 Canada Square
London
E14 5AB

VAT Number: GB444555666
Invoice Number: CWDS-2026-77
Invoice Date: 14 June 2026

Services: \u00a32,000.00
VAT: \u00a30.00
Total: \u00a32,000.00
""",
        expected={
            "document_type": "invoice",
            "supplier_name": "Canary Wharf Data Services",
            "supplier_address": "1 Canada Square, London, E14 5AB",
            "vat_number": "GB444555666",
            "invoice_number": "CWDS-2026-77",
            "invoice_date": "2026-06-14",
            "subtotal_gbp": None,
            "vat_amount_gbp": 0.0,
            "total_amount_gbp": 2000.0,
            "currency": "GBP",
            "confidence": 0.8,
        },
    ),
]


def generate_synthetic_dataset(
    samples_dir: Path = Path("data/samples"),
    ground_truth_path: Path = Path("data/ground_truth.json"),
    image_dir: Path = Path("data/sample_images"),
    degraded_image_dir: Path | None = None,
) -> list[dict[str, object]]:
    samples_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    if degraded_image_dir is not None:
        degraded_image_dir.mkdir(parents=True, exist_ok=True)

    ground_truth = []
    for index, document in enumerate(SYNTHETIC_DOCUMENTS):
        text_path = samples_dir / f"{document.file_stem}.txt"
        image_path = image_dir / f"{document.file_stem}.png"
        text_path.write_text(document.text.strip() + "\n", encoding="utf-8")
        render_text_image(document.text, image_path)
        if degraded_image_dir is not None:
            degraded_path = degraded_image_dir / f"{document.file_stem}.png"
            render_degraded_image(image_path, degraded_path, index=index)
        ground_truth.append(
            {
                "file": str(text_path).replace("\\", "/"),
                "expected": document.expected,
            }
        )

    ground_truth_path.parent.mkdir(parents=True, exist_ok=True)
    ground_truth_path.write_text(json.dumps(ground_truth, indent=2), encoding="utf-8")
    return ground_truth


def render_text_image(text: str, output_path: Path) -> None:
    font = load_font(size=28)
    lines = text.strip().splitlines()
    line_height = 40
    width = 1200
    height = max(700, 80 + line_height * len(lines))

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    y = 40
    for line in lines:
        draw.text((48, y), line, fill="black", font=font)
        y += line_height

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_name in ["arial.ttf", "calibri.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_degraded_image(source_path: Path, output_path: Path, index: int) -> None:
    image = Image.open(source_path).convert("RGB")
    angle = [-2.4, 1.7, -1.5, 2.1, -2.0, 1.3, -1.8, 2.5][index % 8]
    image = image.rotate(
        angle,
        resample=Image.Resampling.BICUBIC,
        expand=True,
        fillcolor=(245, 245, 245),
    )

    width, height = image.size
    scale = [0.72, 0.66, 0.7, 0.63][index % 4]
    low_res = image.resize((int(width * scale), int(height * scale)), Image.Resampling.BILINEAR)
    image = low_res.resize((width, height), Image.Resampling.BICUBIC)
    image = image.filter(ImageFilter.GaussianBlur(radius=0.25 + 0.08 * (index % 3)))

    image = ImageEnhance.Contrast(image).enhance(0.88)
    image = ImageEnhance.Brightness(image).enhance(0.96)
    draw_shadow(image, index=index)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=70, optimize=True)


def draw_shadow(image: Image.Image, index: int) -> None:
    width, height = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    if index % 2 == 0:
        draw.rectangle((0, 0, int(width * 0.32), height), fill=(0, 0, 0, 28))
    else:
        draw.rectangle((0, int(height * 0.68), width, height), fill=(0, 0, 0, 24))
    image.paste(Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB"))
