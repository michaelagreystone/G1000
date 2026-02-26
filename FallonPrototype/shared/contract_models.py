"""
Pydantic models for structured contract extraction.
Based on patterns from Contract RAG with Knowledge Graphs.

These models define the schema for extracting structured data from contracts,
enabling better filtering, search, and analysis.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# Enums for Contract Classification
# ═══════════════════════════════════════════════════════════════════════════════

CLAUSE_TYPES = [
    "Renewal & Termination",
    "Confidentiality & Non-Disclosure",
    "Non-Compete & Exclusivity",
    "Liability & Indemnification",
    "Service-Level Agreements",
    "Default & Remedies",
    "Insurance Requirements",
    "Payment Terms",
    "Governing Law",
    "Force Majeure",
]

CONTRACT_TYPES = [
    "Affiliate Agreement",
    "Development Agreement",
    "Distributor Agreement",
    "Endorsement Agreement",
    "Franchise Agreement",
    "Hosting Agreement",
    "IP License",
    "Joint Venture",
    "License Agreement",
    "Maintenance Agreement",
    "Manufacturing Agreement",
    "Marketing Agreement",
    "Non-Compete Agreement",
    "Outsourcing Agreement",
    "Promotion Agreement",
    "Reseller Agreement",
    "Service Agreement",
    "Sponsorship Agreement",
    "Strategic Alliance",
    "Supply Agreement",
    "Transportation Agreement",
    # Real Estate Specific
    "Loan Agreement",
    "Construction Contract",
    "Lease Agreement",
    "Land Purchase Agreement",
    "JV Operating Agreement",
    "Mezzanine Financing",
    "Preferred Equity Agreement",
    "Property Management Agreement",
    "Architect Agreement",
    "General Contractor Agreement",
]


# ═══════════════════════════════════════════════════════════════════════════════
# Component Models
# ═══════════════════════════════════════════════════════════════════════════════

class Location(BaseModel):
    """Physical location including address, city, state, and country."""
    
    address: Optional[str] = Field(
        None, description="Street address of the location"
    )
    city: Optional[str] = Field(
        None, description="City of the location"
    )
    state: Optional[str] = Field(
        None, description="State or region of the location"
    )
    country: str = Field(
        "US", description="Country (two-letter ISO code)"
    )


class Organization(BaseModel):
    """Organization or party involved in a contract."""
    
    name: str = Field(..., description="Name of the organization or individual")
    location: Optional[Location] = Field(
        None, description="Primary location of the organization"
    )
    role: str = Field(
        ..., description="Role in the contract (e.g., 'borrower', 'lender', 'developer', 'investor')"
    )


class Clause(BaseModel):
    """Represents a clause or provision in a contract."""
    
    summary: str = Field(
        ..., description="Summary of the clause content (no pronouns)"
    )
    clause_type: str = Field(
        ..., description="Type of clause from standard categories"
    )
    key_terms: Optional[List[str]] = Field(
        None, description="Key terms or values mentioned in the clause"
    )


class MonetaryValue(BaseModel):
    """Monetary amount with optional currency."""
    
    amount: float = Field(..., description="Numeric value")
    currency: str = Field("USD", description="Currency code")
    description: Optional[str] = Field(
        None, description="What this amount represents"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Main Contract Model
# ═══════════════════════════════════════════════════════════════════════════════

class ExtractedContract(BaseModel):
    """
    Structured representation of a contract.
    Used for extraction from raw text and storage in the vector store.
    """
    
    summary: str = Field(
        ...,
        description="High-level summary of the contract with relevant facts. No pronouns."
    )
    contract_type: str = Field(
        ...,
        description="Type of contract from the standard list"
    )
    parties: List[Organization] = Field(
        ...,
        description="List of parties involved with their roles"
    )
    effective_date: Optional[str] = Field(
        None,
        description="Contract effective date (YYYY-MM-DD format)"
    )
    end_date: Optional[str] = Field(
        None,
        description="Contract expiration date (YYYY-MM-DD format)"
    )
    duration: Optional[str] = Field(
        None,
        description="Contract duration (ISO 8601 format, e.g., P1Y for 1 year)"
    )
    contract_scope: str = Field(
        ...,
        description="Description of contract scope, rights, duties, and limitations"
    )
    total_amount: Optional[float] = Field(
        None,
        description="Total contract value in dollars"
    )
    monetary_values: Optional[List[MonetaryValue]] = Field(
        None,
        description="All monetary values mentioned (loan amounts, fees, etc.)"
    )
    governing_law: Optional[Location] = Field(
        None,
        description="Jurisdiction governing the contract"
    )
    clauses: Optional[List[Clause]] = Field(
        None,
        description="Key clauses extracted from the contract"
    )
    
    # Real Estate Specific Fields
    property_address: Optional[str] = Field(
        None,
        description="Address of the property involved"
    )
    property_type: Optional[str] = Field(
        None,
        description="Type of property (multifamily, office, retail, hotel, etc.)"
    )
    interest_rate: Optional[float] = Field(
        None,
        description="Interest rate if this is a financing document"
    )
    loan_to_value: Optional[float] = Field(
        None,
        description="LTV ratio if applicable"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def contract_to_metadata(contract: ExtractedContract) -> dict:
    """
    Convert an ExtractedContract to a flat metadata dict for ChromaDB.
    ChromaDB metadata must be flat (str, int, float, bool only).
    """
    metadata = {
        "contract_type": contract.contract_type,
        "summary": contract.summary[:500],  # Truncate for metadata
        "contract_scope": contract.contract_scope[:500],
    }
    
    if contract.effective_date:
        metadata["effective_date"] = contract.effective_date
    if contract.end_date:
        metadata["end_date"] = contract.end_date
    if contract.total_amount:
        metadata["total_amount"] = contract.total_amount
    if contract.property_type:
        metadata["property_type"] = contract.property_type
    if contract.property_address:
        metadata["property_address"] = contract.property_address
    if contract.interest_rate:
        metadata["interest_rate"] = contract.interest_rate
    if contract.loan_to_value:
        metadata["loan_to_value"] = contract.loan_to_value
    
    # Flatten parties to string
    if contract.parties:
        party_names = [p.name for p in contract.parties]
        party_roles = [f"{p.name}:{p.role}" for p in contract.parties]
        metadata["party_names"] = ", ".join(party_names)
        metadata["party_roles"] = ", ".join(party_roles)
    
    # Flatten governing law
    if contract.governing_law:
        if contract.governing_law.state:
            metadata["governing_state"] = contract.governing_law.state
        if contract.governing_law.country:
            metadata["governing_country"] = contract.governing_law.country
    
    return metadata


def contract_to_searchable_text(contract: ExtractedContract) -> str:
    """
    Generate a searchable text representation of the contract for embedding.
    """
    parts = [
        f"Contract Type: {contract.contract_type}",
        f"Summary: {contract.summary}",
        f"Scope: {contract.contract_scope}",
    ]
    
    if contract.parties:
        parties_text = ", ".join(f"{p.name} ({p.role})" for p in contract.parties)
        parts.append(f"Parties: {parties_text}")
    
    if contract.effective_date:
        parts.append(f"Effective Date: {contract.effective_date}")
    if contract.end_date:
        parts.append(f"End Date: {contract.end_date}")
    if contract.total_amount:
        parts.append(f"Total Amount: ${contract.total_amount:,.2f}")
    if contract.property_type:
        parts.append(f"Property Type: {contract.property_type}")
    if contract.property_address:
        parts.append(f"Property Address: {contract.property_address}")
    if contract.interest_rate:
        parts.append(f"Interest Rate: {contract.interest_rate}%")
    
    if contract.clauses:
        clause_summaries = [f"- {c.clause_type}: {c.summary}" for c in contract.clauses]
        parts.append("Key Clauses:\n" + "\n".join(clause_summaries))
    
    return "\n\n".join(parts)
