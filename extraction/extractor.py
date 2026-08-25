"""
LLM Extraction Engine
Uses GPT-4o to extract structured data from document text based on configurable schemas.
"""
import os
import json
from typing import Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --- Extraction Schemas ---

class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float = 0
    total: float = 0

class InvoiceExtraction(BaseModel):
    vendor_name: str = ""
    invoice_number: str = ""
    invoice_date: str = ""
    due_date: str = ""
    line_items: list[InvoiceLineItem] = []
    subtotal: float = 0
    tax: float = 0
    total_amount: float = 0
    payment_terms: str = ""
    confidence: float = 0.0

class ContractExtraction(BaseModel):
    parties: list[str] = []
    effective_date: str = ""
    term_length: str = ""
    key_obligations: list[str] = []
    termination_clauses: list[str] = []
    governing_law: str = ""
    confidence: float = 0.0

class GeneralExtraction(BaseModel):
    document_type: str = ""
    title: str = ""
    key_entities: list[str] = []
    key_dates: list[str] = []
    key_amounts: list[str] = []
    summary: str = ""
    confidence: float = 0.0


def classify_document(text: str) -> str:
    """Classify the document type using an LLM."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Classify this document into ONE of these categories: invoice, contract, report, correspondence, other.\n\nDocument text (first 2000 chars):\n{text[:2000]}\n\nReturn ONLY the category name."
        }],
        temperature=0
    )
    return (response.choices[0].message.content or "other").strip().lower()


def extract_structured_data(text: str, doc_type: Optional[str] = None) -> dict:
    """
    Extract structured data from document text using LLM + schema enforcement.
    """
    if not doc_type:
        doc_type = classify_document(text)
    
    schema_map = {
        "invoice": InvoiceExtraction,
        "contract": ContractExtraction,
    }
    
    schema_class = schema_map.get(doc_type)
    
    if schema_class:
        schema_json = schema_class.model_json_schema()
        prompt = f"""Extract structured data from this {doc_type} document.
Output MUST be valid JSON matching this schema:
{json.dumps(schema_json, indent=2)}

IMPORTANT:
- Only extract information that is EXPLICITLY present in the text.
- Do not infer or guess missing values.
- Set confidence to a float between 0.0 and 1.0 indicating your overall extraction confidence.

Document text:
{text[:8000]}

Return ONLY valid JSON."""
    else:
        schema_json = GeneralExtraction.model_json_schema()
        prompt = f"""Extract key information from this document.
Output MUST be valid JSON matching this schema:
{json.dumps(schema_json, indent=2)}

Document text:
{text[:8000]}

Return ONLY valid JSON."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content or "{}"
    extraction = json.loads(content)
    extraction["_document_type"] = doc_type
    
    return extraction
