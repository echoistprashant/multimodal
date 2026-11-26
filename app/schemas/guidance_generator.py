"""Field Extraction Guidance Generator.

Reflects upon Pydantic model schemas to generate targeted field-level instructions,
format hints, and contextual guidelines for prompt injection.
"""

from typing import List, Type
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from app.schemas.guidance_schema import FieldGuidance

FIELD_SYNONYMS = {
    "invoice_number": ["invoice #", "bill no", "inv no", "bill number", "tax invoice no"],
    "po_number": ["p.o. #", "purchase order", "po no", "order ref"],
    "document_date": ["invoice date", "bill date", "date of issue", "tx date"],
    "due_date": ["payment due", "due by", "pay before", "maturity date"],
    "total_amount": ["grand total", "total payable", "amount due", "net amount", "balance due"],
    "subtotal": ["net total", "taxable amount", "sub-total", "charges before tax"],
    "tax_amount": ["vat", "gst", "sales tax", "tax total"],
    "merchant_name": ["store", "vendor", "retailer", "merchant", "seller"],
    "patient_name": ["patient", "patient legal name", "admitted patient"],
}


def generate_schema_guidance(model_cls: Type[BaseModel]) -> List[FieldGuidance]:
    """Generate extraction guidance annotations for each property in a Pydantic model."""
    guidance_list: List[FieldGuidance] = []

    for name, field_info in model_cls.model_fields.items():
        is_required = field_info.default is PydanticUndefined and field_info.default_factory is None
        desc = field_info.description or f"Value for {name}"
        data_type = str(field_info.annotation or "Any")

        # Infer format hints
        format_hint = None
        if "date" in name.lower():
            format_hint = "ISO 8601 format: YYYY-MM-DD"
        elif "amount" in name.lower() or "price" in name.lower() or "subtotal" in name.lower():
            format_hint = "Numeric decimal/float (e.g. 1250.00). Do not include currency symbols ($)."
        elif "currency" in name.lower():
            format_hint = "3-letter ISO 4217 currency code (e.g. USD, EUR, GBP, INR)."

        synonyms = FIELD_SYNONYMS.get(name, [])

        guidance_list.append(
            FieldGuidance(
                field_name=name,
                data_type=data_type,
                description=desc,
                required=is_required,
                format_hint=format_hint,
                synonyms=synonyms,
                null_if_absent=True,
            )
        )

    return guidance_list


def format_guidance_for_prompt(guidance_list: List[FieldGuidance]) -> str:
    """Format structured field guidance into instructions for LLM system prompts."""
    lines: List[str] = [
        "### Field Extraction Guidance Rules:",
        "- STRICT POLICY: If a field is not explicitly present in the document, emit `null`. NEVER hallucinate placeholder values such as 'N/A', 'None', or '0.00'.",
    ]

    for g in guidance_list:
        req_str = "REQUIRED" if g.required else "OPTIONAL"
        hint_str = f" [Format: {g.format_hint}]" if g.format_hint else ""
        syn_str = f" (Common labels: {', '.join(g.synonyms)})" if g.synonyms else ""
        lines.append(f"- **{g.field_name}** ({req_str}){hint_str}{syn_str}: {g.description}")

    return "\n".join(lines)
