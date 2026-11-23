"""Unit tests for Phase 5: Image Preprocessing, OCR Engines, Aggregation, and CER/WER Metrics."""

import io
from PIL import Image
import pytest

from app.evaluation.ocr_metrics import compute_cer, compute_wer, evaluate_transcription
from app.ocr.aggregator import TokenAggregator
from app.ocr.mock_or_deep import DeepOCREngine
from app.parser.schema import BoundingBox, Token
from app.preprocess.binarize import binarize_document, compute_otsu_threshold
from app.preprocess.denoise import apply_gaussian_denoise, convert_to_grayscale
from app.preprocess.deskew import deskew_image


@pytest.fixture
def sample_test_image_bytes() -> bytes:
    """Create a simple in-memory PNG image for preprocessing tests."""
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    # Draw simple dark pixel box in center
    for x in range(50, 150):
        for y in range(30, 70):
            img.putpixel((x, y), (10, 10, 10))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_grayscale_and_denoise_filters(sample_test_image_bytes: bytes) -> None:
    """Verify grayscale and Gaussian denoising transformation."""
    gray_bytes = convert_to_grayscale(sample_test_image_bytes)
    with Image.open(io.BytesIO(gray_bytes)) as img:
        assert img.mode == "L"

    denoised_bytes = apply_gaussian_denoise(gray_bytes, radius=1.0)
    with Image.open(io.BytesIO(denoised_bytes)) as img:
        assert img.mode == "L"
        assert img.size == (200, 100)


def test_otsu_threshold_and_binarization(sample_test_image_bytes: bytes) -> None:
    """Verify Otsu threshold computation and 1-bit binary output."""
    binary_bytes = binarize_document(sample_test_image_bytes, autocontrast=True)
    with Image.open(io.BytesIO(binary_bytes)) as img:
        assert img.mode == "1"
        assert img.size == (200, 100)


def test_deskewing_angle_correction(sample_test_image_bytes: bytes) -> None:
    """Verify deskew image rotation with positive angle."""
    corrected_bytes, angle = deskew_image(sample_test_image_bytes, known_angle=5.0)
    assert angle == 5.0
    with Image.open(io.BytesIO(corrected_bytes)) as img:
        # Rotated with expand=True increases dimensions
        assert img.width > 200 or img.height > 100


def test_cer_and_wer_evaluation_metrics() -> None:
    """Verify CER and WER computation on known ground truth strings."""
    # 1. Exact match
    res_exact = evaluate_transcription("INVOICE 1042", "INVOICE 1042")
    assert res_exact["cer"] == 0.0
    assert res_exact["wer"] == 0.0
    assert res_exact["accuracy"] == 1.0

    # 2. Single digit character error (e.g., 'O' vs '0')
    cer_digit = compute_cer("T0TAL", "TOTAL")
    assert cer_digit == 0.2  # 1 substitution out of 5 chars = 0.2

    # 3. Word Error Rate
    ref_sentence = "Grand Total Amount Due"
    hyp_sentence = "Grand Amount Due"  # 1 deletion out of 4 words = 0.25
    wer_val = compute_wer(ref_sentence, hyp_sentence)
    assert wer_val == 0.25


def test_token_aggregator_line_grouping() -> None:
    """Verify word tokens on the same horizontal line are clustered together."""
    tokens = [
        Token(text="Total:", bbox=BoundingBox(x0=0.6, y0=0.801, x1=0.7, y1=0.83)),
        Token(text="Tax:", bbox=BoundingBox(x0=0.6, y0=0.750, x1=0.7, y1=0.78)),
        Token(text="180.00", bbox=BoundingBox(x0=0.75, y0=0.752, x1=0.9, y1=0.78)),
        Token(text="1180.00", bbox=BoundingBox(x0=0.75, y0=0.800, x1=0.9, y1=0.83)),
    ]

    aggregator = TokenAggregator(line_y_threshold=0.015)
    lines = aggregator.group_tokens_into_lines(tokens)
    assert len(lines) == 2

    serialized = aggregator.serialize_lines_to_text(lines)
    assert len(serialized) == 2
    # Verify line 1 text
    assert serialized[0][0] == "Tax: 180.00"
    # Verify line 2 text
    assert serialized[1][0] == "Total: 1180.00"


def test_deep_ocr_engine_adapter() -> None:
    """Verify DeepOCREngine returns normalized tokens with confidences."""
    import asyncio
    engine = DeepOCREngine(engine_name="paddleocr")
    assert engine.name == "paddleocr"

    async def _test() -> None:
        tokens = await engine.extract_tokens(b"dummy_image_data", page_no=1)
        assert len(tokens) >= 5
        for t in tokens:
            assert 0.0 <= t.bbox.x0 <= t.bbox.x1 <= 1.0
            assert 0.0 <= t.bbox.y0 <= t.bbox.y1 <= 1.0
            assert 0.0 <= t.confidence <= 1.0

        full_text = await engine.extract_text(b"dummy_image_data")
        assert "INVOICE" in full_text
        assert "1180.00" in full_text

    asyncio.run(_test())
