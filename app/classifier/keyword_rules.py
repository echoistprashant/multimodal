"""Lexical Keyword and Regex Pattern Classifier Rules.

Analyzes text tokens against diagnostic regular expression patterns and term frequencies
to compute domain category affinities.
"""

import re
from typing import Dict, List, Set, Tuple
from app.classifier.schema import DocumentType

DOCUMENT_PATTERNS: Dict[DocumentType, List[Tuple[re.Pattern, float]]] = {
    DocumentType.INVOICE: [
        (re.compile(r"\b(?:tax\s+)?invoice\b", re.I), 3.0),
        (re.compile(r"\bbill\s+to\b", re.I), 2.0),
        (re.compile(r"\binvoice\s+(?:no|number|#)\b", re.I), 3.0),
        (re.compile(r"\bdue\s+date\b", re.I), 2.0),
        (re.compile(r"\bp\.?o\.?\s+(?:no|number|#)\b", re.I), 2.5),
        (re.compile(r"\bremit\s+to\b", re.I), 2.0),
        (re.compile(r"\bamount\s+due\b", re.I), 2.0),
        (re.compile(r"\bgst(?:in)?\b", re.I), 1.5),
    ],
    DocumentType.RECEIPT: [
        (re.compile(r"\breceipt\b", re.I), 3.0),
        (re.compile(r"\bcashier\b", re.I), 2.5),
        (re.compile(r"\bregister\s+#?\d+\b", re.I), 2.5),
        (re.compile(r"\bchange\s+due\b", re.I), 2.5),
        (re.compile(r"\b(?:visa|mastercard|amex|cash)\s+(?:tender|paid|usd|\$)\b", re.I), 2.0),
        (re.compile(r"\bstore\s+#?\d+\b", re.I), 2.0),
        (re.compile(r"\bmerchant\s+id\b", re.I), 2.0),
    ],
    DocumentType.MEDICAL_BILL: [
        (re.compile(r"\bpatient\s+(?:name|id|#)\b", re.I), 3.0),
        (re.compile(r"\bhospital|clinic\b", re.I), 2.0),
        (re.compile(r"\bphysician|doctor\b", re.I), 2.0),
        (re.compile(r"\badmission\s+date\b", re.I), 2.5),
        (re.compile(r"\bdischarge\s+date\b", re.I), 2.5),
        (re.compile(r"\bcopay(?:ment)?\b", re.I), 3.0),
        (re.compile(r"\binsurance\s+(?:claim|policy|id)\b", re.I), 2.5),
        (re.compile(r"\bdiagnosis|treatment\b", re.I), 2.0),
    ],
    DocumentType.FINANCIAL_REPORT: [
        (re.compile(r"\bbalance\s+sheet\b", re.I), 3.5),
        (re.compile(r"\bincome\s+statement\b", re.I), 3.5),
        (re.compile(r"\bcash\s+flows?\b", re.I), 3.0),
        (re.compile(r"\bfiscal\s+year\b", re.I), 2.5),
        (re.compile(r"\bconsolidated\s+statements?\b", re.I), 3.0),
        (re.compile(r"\bebitda\b", re.I), 2.5),
        (re.compile(r"\bshareholders?'?\s+equity\b", re.I), 3.0),
    ],
}


def score_text_by_keywords(text: str) -> Tuple[Dict[str, float], List[str]]:
    """Score text against diagnostic regex patterns for each candidate document type.

    Returns:
        tuple (scores_dict, matched_keywords_list)
    """
    scores: Dict[str, float] = {dtype.value: 0.0 for dtype in DOCUMENT_PATTERNS}
    all_matched: Set[str] = set()

    for dtype, patterns in DOCUMENT_PATTERNS.items():
        for pattern, weight in patterns:
            matches = pattern.findall(text)
            if matches:
                scores[dtype.value] += len(matches) * weight
                for m in matches[:3]:
                    all_matched.add(m.strip().lower())

    return scores, sorted(list(all_matched))
