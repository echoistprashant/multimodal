"""Prompt Builder with Dynamic JSON Schema Injection.

Constructs production extraction prompts by dynamically injecting JSON schema contracts,
system instructions, and in-context few-shot demonstration exemplars.
"""

import json
from typing import Type
from pydantic import BaseModel

from app.extraction.prompt_schema import ExtractionPromptContext, FormattedExtractionPrompt
from app.schemas.guidance_generator import format_guidance_for_prompt, generate_schema_guidance


class ExtractionPromptBuilder:
    """Builder generating standardized extraction prompts for text LLMs and vision VLMs."""

    DEFAULT_SYSTEM_ROLE = (
        "You are an expert Document Intelligence AI assistant specialized in structured information extraction. "
        "Your task is to analyze document text or layout data and extract structured entity fields into valid JSON "
        "conforming strictly to the provided JSON Schema specification."
    )

    def build_prompt(self, context: ExtractionPromptContext) -> FormattedExtractionPrompt:
        """Construct system and user prompt strings from context."""
        schema_json_str = json.dumps(context.json_schema, indent=2)

        system_parts = [
            self.DEFAULT_SYSTEM_ROLE,
            "\n### Target Output JSON Schema:",
            f"```json\n{schema_json_str}\n```",
        ]

        if context.field_guidance:
            system_parts.append(f"\n{context.field_guidance}")

        system_parts.extend([
            "\n### Strict Operational Constraints:",
            "1. Output ONLY a valid, parseable JSON object matching the schema above.",
            "2. Never hallucinate default values. If a field is not found in the source text, set it to `null`.",
            "3. Do not include markdown code fence formatting (```json) unless explicitly required by the caller.",
            "4. Do not prefix or suffix the JSON with explanations, conversational filler, or commentary.",
        ])

        system_prompt = "\n".join(system_parts)

        # Build User Prompt
        user_parts = []
        if context.few_shot_examples:
            user_parts.append("### Reference Examples:")
            for idx, ex in enumerate(context.few_shot_examples, 1):
                user_parts.append(f"Example {idx}:\nDocument:\n{ex.get('input', '')}\nOutput:\n{json.dumps(ex.get('output', {}), indent=2)}")

        user_parts.append(
            f"### Document Text to Extract ({context.doc_type.upper()}):\n"
            f"<document_content>\n{context.document_text}\n</document_content>\n\n"
            f"Extract all fields for document type '{context.doc_type}' as valid JSON:"
        )

        user_prompt = "\n\n".join(user_parts)

        return FormattedExtractionPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            target_schema_name=context.doc_type,
        )

    @classmethod
    def from_model(cls, model_cls: Type[BaseModel], doc_text: str) -> FormattedExtractionPrompt:
        """Convenience factory method directly compiling prompt from a Pydantic model class."""
        guidance_list = generate_schema_guidance(model_cls)
        guidance_str = format_guidance_for_prompt(guidance_list)

        doc_type = getattr(model_cls, "__doc_type__", model_cls.__name__.lower().replace("schema", ""))

        context = ExtractionPromptContext(
            doc_type=doc_type,
            document_text=doc_text,
            json_schema=model_cls.model_json_schema(),
            field_guidance=guidance_str,
        )
        return cls().build_prompt(context)
