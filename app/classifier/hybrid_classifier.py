"""Hybrid Document Classifier Combining Lexical Patterns and Spatial Layout Cues.

Integrates keyword pattern scoring, table existence signals, and aspect ratio features
to output calibrated category classifications.
"""

from typing import List, Optional
from app.classifier.keyword_rules import score_text_by_keywords
from app.classifier.schema import ClassificationResult, DocumentType
from app.layout.schema import LayoutBlock
from app.tables.grid_schema import StructuredTable


class HybridDocumentClassifier:
    """Multi-feature document type classifier."""

    def classify_document(
        self,
        text: str,
        blocks: Optional[List[LayoutBlock]] = None,
        tables: Optional[List[StructuredTable]] = None,
        aspect_ratio: float = 1.414,  # Standard A4 / Letter portrait ratio (height / width)
    ) -> ClassificationResult:
        """Classify a document into one of the supported domain document categories.

        Args:
            text: Consolidated text content from all pages.
            blocks: Optional list of segmented layout blocks.
            tables: Optional list of reconstructed tables.
            aspect_ratio: Page height divided by page width.

        Returns:
            ClassificationResult with predicted category, confidence, and explanation.
        """
        scores, matched_keywords = score_text_by_keywords(text)

        # 1. Structural layout adjustments
        # Receipts are typically narrow POS paper strips with aspect ratio > 2.0
        if aspect_ratio >= 2.0:
            scores[DocumentType.RECEIPT.value] += 4.0

        # Presence of structured tables strongly boosts Invoices and Financial Reports
        if tables and len(tables) > 0:
            scores[DocumentType.INVOICE.value] += 2.0
            scores[DocumentType.FINANCIAL_REPORT.value] += 1.5

        # Check top predicted category
        best_type_str = max(scores, key=lambda k: scores[k])
        max_score = scores[best_type_str]

        # Calculate softmax-like confidence or ratio
        total_score = sum(scores.values())
        if total_score <= 1.0 or max_score == 0.0:
            return ClassificationResult(
                predicted_type=DocumentType.UNKNOWN,
                confidence=0.50,
                matched_keywords=[],
                feature_scores=scores,
                explanation="Insufficient diagnostic textual patterns or structural cues to classify document.",
            )

        # Normalize confidence to [0.50, 0.99]
        confidence = round(min(0.50 + 0.49 * (max_score / total_score), 0.99), 4)
        predicted_type = DocumentType(best_type_str)

        explanation = (
            f"Classified as '{predicted_type.value}' with confidence {confidence * 100:.1f}%. "
            f"Matched terms: {', '.join(matched_keywords[:4]) if matched_keywords else 'None'}."
        )

        return ClassificationResult(
            predicted_type=predicted_type,
            confidence=confidence,
            matched_keywords=matched_keywords,
            feature_scores=scores,
            explanation=explanation,
        )
