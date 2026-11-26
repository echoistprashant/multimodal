"""Unit tests for Phase 9 Part 9.2: Text LLM Extractor and Retry Handler."""

import asyncio
import pytest

from app.extraction.prompt_builder import ExtractionPromptBuilder
from app.extraction.retry import retry_with_backoff
from app.extraction.text_llm import TextLLMExtractor
from app.schemas.invoice import InvoiceSchema


def test_text_llm_extractor_mock() -> None:
    """Verify text LLM extractor parses invoice fields deterministically."""
    async def _run() -> None:
        doc_text = "INVOICE #9981\nVendor: Cloud Tech Solutions\nTotal Amount: $2,500.00"
        prompt = ExtractionPromptBuilder.from_model(InvoiceSchema, doc_text)

        extractor = TextLLMExtractor(model_name="mock-fast-extractor")
        result = await extractor.extract(prompt)

        assert result.success is True
        assert result.model_name == "mock-fast-extractor"
        assert result.parsed_json["invoice_number"] == "9981"
        assert result.parsed_json["total_amount"] == 2500.00
        assert result.parsed_json["vendor"]["name"] == "Cloud Tech Solutions"

    asyncio.run(_run())


def test_retry_with_backoff_transient_recovery() -> None:
    """Verify retry handler recovers after transient failures."""
    async def _run() -> None:
        attempts = 0

        async def flaky_call() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError("Temporary DNS timeout")
            return "SUCCESS"

        result = await retry_with_backoff(
            flaky_call,
            max_retries=3,
            initial_delay_sec=0.01,
            retryable_exceptions=(ConnectionError,),
        )
        assert result == "SUCCESS"
        assert attempts == 3

    asyncio.run(_run())


def test_retry_with_backoff_exhaustion() -> None:
    """Verify retry handler raises when failures exceed max_retries."""
    async def _run() -> None:
        async def always_fails() -> None:
            raise ValueError("Fatal error")

        with pytest.raises(ValueError):
            await retry_with_backoff(
                always_fails,
                max_retries=2,
                initial_delay_sec=0.01,
                retryable_exceptions=(ValueError,),
            )

    asyncio.run(_run())
