"""
Validation & Business Rules Engine
Validates extracted data against type constraints and domain-specific rules.
Routes documents to auto-approve or human-review based on confidence.
"""
from datetime import datetime
from typing import Optional


class ValidationResult:
    def __init__(self):
        self.errors: list[dict] = []
        self.warnings: list[dict] = []
        self.passed: bool = True
    
    def add_error(self, field: str, message: str):
        self.errors.append({"field": field, "message": message, "severity": "error"})
        self.passed = False
    
    def add_warning(self, field: str, message: str):
        self.warnings.append({"field": field, "message": message, "severity": "warning"})
    
    def to_dict(self):
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "total_issues": len(self.errors) + len(self.warnings)
        }


def validate_date(date_str: str, field_name: str, result: ValidationResult):
    """Validate a date string."""
    if not date_str:
        result.add_warning(field_name, f"{field_name} is empty")
        return
    
    # Try common date formats
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"]:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # Check if date is plausible (within 10 years)
            if parsed.year < 2015 or parsed.year > 2035:
                result.add_warning(field_name, f"Date {date_str} seems out of expected range")
            return
        except ValueError:
            continue
    
    result.add_warning(field_name, f"Could not parse date: {date_str}")


def validate_amount(amount: float, field_name: str, result: ValidationResult, max_expected: float = 1_000_000):
    """Validate a monetary amount."""
    if amount < 0:
        result.add_error(field_name, f"{field_name} is negative: {amount}")
    if amount > max_expected:
        result.add_warning(field_name, f"{field_name} ({amount}) exceeds expected max ({max_expected})")


def validate_invoice(extraction: dict) -> ValidationResult:
    """Apply invoice-specific business rules."""
    result = ValidationResult()
    
    # Required fields
    if not extraction.get("vendor_name"):
        result.add_error("vendor_name", "Vendor name is missing")
    if not extraction.get("invoice_number"):
        result.add_error("invoice_number", "Invoice number is missing")
    
    # Date validation
    validate_date(extraction.get("invoice_date", ""), "invoice_date", result)
    validate_date(extraction.get("due_date", ""), "due_date", result)
    
    # Amount validation
    total = extraction.get("total_amount", 0)
    validate_amount(total, "total_amount", result)
    
    # Line item consistency
    line_items = extraction.get("line_items", [])
    computed_subtotal = sum(item.get("total", 0) for item in line_items)
    declared_subtotal = extraction.get("subtotal", 0)
    
    if line_items and declared_subtotal > 0:
        if abs(computed_subtotal - declared_subtotal) > 0.01:
            result.add_warning("subtotal", f"Line item totals ({computed_subtotal:.2f}) don't match declared subtotal ({declared_subtotal:.2f})")
    
    # Tax sanity check
    tax = extraction.get("tax", 0)
    if total > 0 and tax > 0:
        tax_rate = tax / (total - tax) if total != tax else 0
        if tax_rate > 0.25:
            result.add_warning("tax", f"Tax rate appears unusually high ({tax_rate*100:.1f}%)")
    
    return result


def validate_contract(extraction: dict) -> ValidationResult:
    """Apply contract-specific business rules."""
    result = ValidationResult()
    
    if not extraction.get("parties") or len(extraction.get("parties", [])) < 2:
        result.add_error("parties", "Contract must have at least 2 parties")
    
    validate_date(extraction.get("effective_date", ""), "effective_date", result)
    
    if not extraction.get("termination_clauses"):
        result.add_warning("termination_clauses", "No termination clauses found")
    
    if not extraction.get("key_obligations"):
        result.add_warning("key_obligations", "No key obligations extracted")
    
    return result


def validate_extraction(extraction: dict) -> dict:
    """
    Main validation entry point. Routes to the correct validator by document type.
    Returns the validation result plus a routing decision.
    """
    doc_type = extraction.get("_document_type", "other")
    confidence = extraction.get("confidence", 0.5)
    
    validators = {
        "invoice": validate_invoice,
        "contract": validate_contract,
    }
    
    validator = validators.get(doc_type)
    if validator:
        result = validator(extraction)
    else:
        result = ValidationResult()  # No specific rules for unknown types
    
    # Routing decision based on confidence and validation
    if result.passed and confidence >= 0.8:
        routing = "auto-approve"
    elif not result.passed or confidence < 0.5:
        routing = "detailed-review"
    else:
        routing = "quick-review"
    
    return {
        "validation": result.to_dict(),
        "routing": routing,
        "confidence": confidence,
        "document_type": doc_type
    }
