"""
Excel Export (Phase 5)

Generates professionally formatted Excel workbooks from pro forma data.
Six sheets: Summary, Revenue, Costs, Financing, Returns, Assumptions & Sources.
"""

import io
from openpyxl import Workbook
from openpyxl.styles import Font, Fill, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ═══════════════════════════════════════════════════════════════════════════════
# Style Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Label-based fills
FILL_CONFIRMED = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")
FILL_ESTIMATED = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
FILL_CALCULATED = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
FILL_MISSING = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")

# Sensitivity table fills
FILL_GREEN = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
FILL_YELLOW = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
FILL_RED = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

# Header fills
FILL_HEADER = PatternFill(start_color="4F4F4F", end_color="4F4F4F", fill_type="solid")
FILL_SECTION = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")

# Fonts
FONT_HEADER = Font(bold=True, color="FFFFFF", size=11)
FONT_SECTION = Font(bold=True, size=11)
FONT_TITLE = Font(bold=True, size=16)
FONT_METRIC = Font(bold=True, size=14)
FONT_NORMAL = Font(size=10)

# Borders
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

# Column widths
COLUMN_WIDTHS = {
    "A": 35,  # Variable name
    "B": 15,  # Value
    "C": 12,  # Unit
    "D": 14,  # Label
    "E": 50,  # Source
}

LABEL_FILLS = {
    "confirmed": FILL_CONFIRMED,
    "estimated": FILL_ESTIMATED,
    "calculated": FILL_CALCULATED,
    "missing": FILL_MISSING,
}

COLOR_FILLS = {
    "green": FILL_GREEN,
    "yellow": FILL_YELLOW,
    "red": FILL_RED,
    "neutral": FILL_CALCULATED,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _set_column_widths(ws):
    """Set standard column widths for a worksheet."""
    for col, width in COLUMN_WIDTHS.items():
        ws.column_dimensions[col].width = width


def _add_header_row(ws, row: int, headers: list[str]):
    """Add a styled header row."""
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER
    return row + 1


def _add_section_header(ws, row: int, title: str):
    """Add a section header spanning columns A-E."""
    cell = ws.cell(row=row, column=1, value=title)
    cell.font = FONT_SECTION
    cell.fill = FILL_SECTION
    for col in range(1, 6):
        ws.cell(row=row, column=col).fill = FILL_SECTION
        ws.cell(row=row, column=col).border = THIN_BORDER
    return row + 1


def _add_value_row(ws, row: int, name: str, field: dict | None):
    """Add a data row with label-based coloring."""
    if field is None:
        ws.cell(row=row, column=1, value=name).font = FONT_NORMAL
        ws.cell(row=row, column=2, value="N/A")
        return row + 1
    
    if isinstance(field, dict):
        value = field.get("value")
        unit = field.get("unit", "")
        label = field.get("label", "estimated")
        source = field.get("source", "")
    else:
        value = field
        unit = ""
        label = "confirmed"
        source = ""
    
    # Format value
    if isinstance(value, float):
        if abs(value) >= 1_000_000:
            formatted_value = f"${value:,.0f}"
        elif abs(value) >= 1000:
            formatted_value = f"${value:,.0f}" if unit == "$" else f"{value:,.2f}"
        else:
            formatted_value = f"{value:.2f}" if value != int(value) else str(int(value))
    elif value is None:
        formatted_value = "—"
    else:
        formatted_value = str(value)
    
    # Get fill based on label
    fill = LABEL_FILLS.get(label, FILL_ESTIMATED)
    
    # Write cells
    cells = [
        (1, name),
        (2, formatted_value),
        (3, unit),
        (4, label),
        (5, source),
    ]
    
    for col, val in cells:
        cell = ws.cell(row=row, column=col, value=val)
        cell.font = FONT_NORMAL
        cell.fill = fill
        cell.border = THIN_BORDER
        if col == 2:
            cell.alignment = Alignment(horizontal="right")
    
    return row + 1


def _format_currency(value: float | None) -> str:
    """Format a number as currency."""
    if value is None:
        return "—"
    if abs(value) >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif abs(value) >= 1000:
        return f"${value/1000:.0f}K"
    else:
        return f"${value:.0f}"


def _format_percent(value: float | None) -> str:
    """Format a number as percentage."""
    if value is None:
        return "—"
    return f"{value:.1f}%"


def _val(section: dict, key: str, default=None):
    """Safely extract value from a pro forma field."""
    if not isinstance(section, dict):
        return default
    field = section.get(key)
    if field is None:
        return default
    if isinstance(field, dict):
        val = field.get("value")
        return val if val is not None else default
    return field


# ═══════════════════════════════════════════════════════════════════════════════
# Sheet Builders
# ═══════════════════════════════════════════════════════════════════════════════

def _build_summary_sheet(wb: Workbook, export_data: dict):
    """Build the Summary sheet with headline metrics."""
    ws = wb.active
    ws.title = "Summary"
    _set_column_widths(ws)
    
    pro_forma = export_data.get("pro_forma", {})
    summary = pro_forma.get("project_summary", {})
    returns = pro_forma.get("return_metrics", {})
    costs = pro_forma.get("cost_assumptions", {})
    
    row = 1
    
    # Title
    deal_name = summary.get("deal_name", "Development Pro Forma")
    cell = ws.cell(row=row, column=1, value=deal_name)
    cell.font = FONT_TITLE
    row += 2
    
    # Headline metrics
    metrics = [
        ("Levered LP IRR", _format_percent(_val(returns, "project_irr_levered_pct"))),
        ("LP Equity Multiple", f"{_val(returns, 'equity_multiple_lp', 0):.2f}x"),
        ("Profit on Cost", _format_percent(_val(returns, "profit_on_cost_pct"))),
        ("Total Project Cost", _format_currency(_val(costs, "total_project_cost"))),
    ]
    
    for label, value in metrics:
        cell = ws.cell(row=row, column=1, value=label)
        cell.font = FONT_METRIC
        cell = ws.cell(row=row, column=2, value=value)
        cell.font = FONT_METRIC
        cell.alignment = Alignment(horizontal="right")
        row += 1
    
    row += 1
    
    # Project parameters
    row = _add_section_header(ws, row, "PROJECT PARAMETERS")
    
    params = [
        ("Market", summary.get("market", "—")),
        ("Program Type", summary.get("program_type", "—")),
        ("Total GFA", f"{_val(summary, 'total_gfa_sf', 0):,} SF"),
        ("Unit Count", _val(summary, "unit_count") or "N/A"),
        ("Rentable SF", _val(summary, "rentable_sf") or "N/A"),
        ("Hotel Keys", _val(summary, "total_keys") or "N/A"),
        ("Construction Start", _val(summary, "construction_start") or "TBD"),
        ("Construction Duration", f"{_val(summary, 'construction_duration_months', 0)} months"),
    ]
    
    for label, value in params:
        ws.cell(row=row, column=1, value=label).font = FONT_NORMAL
        ws.cell(row=row, column=2, value=str(value)).font = FONT_NORMAL
        row += 1
    
    row += 1
    
    # Notes
    notes = summary.get("notes", "")
    if notes:
        row = _add_section_header(ws, row, "NOTES")
        ws.cell(row=row, column=1, value=notes).font = FONT_NORMAL
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
        row += 1
    
    # Warnings
    warnings = export_data.get("warnings", [])
    if warnings:
        row += 1
        row = _add_section_header(ws, row, "WARNINGS")
        for warning in warnings:
            ws.cell(row=row, column=1, value=warning).font = FONT_NORMAL
            ws.cell(row=row, column=1).fill = FILL_YELLOW
            row += 1


def _build_revenue_sheet(wb: Workbook, export_data: dict):
    """Build the Revenue assumptions sheet."""
    ws = wb.create_sheet("Revenue")
    _set_column_widths(ws)
    
    pro_forma = export_data.get("pro_forma", {})
    revenue = pro_forma.get("revenue_assumptions", {})
    
    row = 1
    row = _add_header_row(ws, row, ["Assumption", "Value", "Unit", "Label", "Source"])
    
    fields = [
        ("Monthly Rent ($/SF)", "rent_psf_monthly"),
        ("Annual Rent NNN ($/SF)", "rent_psf_annual_nnn"),
        ("ADR (Hotel)", "adr"),
        ("Stabilized Occupancy", "stabilized_occupancy_pct"),
        ("Lease-Up Period", "lease_up_months"),
        ("Annual Rent Growth", "annual_rent_growth_pct"),
        ("Other Income per Unit", "other_income_per_unit_monthly"),
    ]
    
    for display_name, key in fields:
        row = _add_value_row(ws, row, display_name, revenue.get(key))


def _build_costs_sheet(wb: Workbook, export_data: dict):
    """Build the Costs sheet."""
    ws = wb.create_sheet("Costs")
    _set_column_widths(ws)
    
    pro_forma = export_data.get("pro_forma", {})
    costs = pro_forma.get("cost_assumptions", {})
    
    row = 1
    row = _add_header_row(ws, row, ["Cost Item", "Value", "Unit", "Label", "Source"])
    
    fields = [
        ("Land Cost (Total)", "land_cost_total"),
        ("Hard Cost ($/SF)", "hard_cost_psf"),
        ("Hard Cost (Total)", "hard_cost_total"),
        ("Soft Cost (% of Hard)", "soft_cost_pct_of_hard"),
        ("Soft Cost (Total)", "soft_cost_total"),
        ("Developer Fee (%)", "developer_fee_pct"),
        ("Developer Fee (Total)", "developer_fee_total"),
        ("Contingency (%)", "contingency_pct"),
        ("Contingency (Total)", "contingency_total"),
        ("TOTAL PROJECT COST", "total_project_cost"),
    ]
    
    for display_name, key in fields:
        row = _add_value_row(ws, row, display_name, costs.get(key))
    
    # Bold the total row
    for col in range(1, 6):
        ws.cell(row=row-1, column=col).font = Font(bold=True, size=10)


def _build_financing_sheet(wb: Workbook, export_data: dict):
    """Build the Financing sheet."""
    ws = wb.create_sheet("Financing")
    _set_column_widths(ws)
    
    pro_forma = export_data.get("pro_forma", {})
    financing = pro_forma.get("financing_assumptions", {})
    
    row = 1
    row = _add_header_row(ws, row, ["Item", "Value", "Unit", "Label", "Source"])
    
    # Construction loan section
    row = _add_section_header(ws, row, "CONSTRUCTION LOAN")
    
    loan_fields = [
        ("Loan-to-Cost", "construction_loan_ltc_pct"),
        ("Loan Amount", "construction_loan_amount"),
        ("Interest Rate", "construction_loan_rate_pct"),
        ("Carry Cost (Total)", "carry_cost_total"),
    ]
    
    for display_name, key in loan_fields:
        row = _add_value_row(ws, row, display_name, financing.get(key))
    
    # Equity section
    row = _add_section_header(ws, row, "EQUITY")
    
    equity_fields = [
        ("Total Equity Required", "equity_required"),
        ("LP Equity (%)", "lp_equity_pct"),
        ("LP Equity ($)", "lp_equity_amount"),
        ("GP Equity (%)", "gp_equity_pct"),
        ("GP Equity ($)", "gp_equity_amount"),
    ]
    
    for display_name, key in equity_fields:
        row = _add_value_row(ws, row, display_name, financing.get(key))


def _build_returns_sheet(wb: Workbook, export_data: dict):
    """Build the Returns sheet with sensitivity table."""
    ws = wb.create_sheet("Returns")
    _set_column_widths(ws)
    
    pro_forma = export_data.get("pro_forma", {})
    returns = pro_forma.get("return_metrics", {})
    
    row = 1
    row = _add_header_row(ws, row, ["Metric", "Value", "Unit", "Label", "Source"])
    
    fields = [
        ("Exit Cap Rate", "exit_cap_rate_pct"),
        ("Exit Year", "exit_year"),
        ("Stabilized NOI", "stabilized_noi"),
        ("Gross Exit Value", "gross_exit_value"),
        ("Net Exit Value", "net_exit_value"),
        ("Total Profit", "total_profit"),
        ("Profit on Cost", "profit_on_cost_pct"),
        ("Development Spread", "development_spread_bps"),
        ("Project IRR (Levered)", "project_irr_levered_pct"),
        ("LP Equity Multiple", "equity_multiple_lp"),
        ("LP IRR", "lp_irr_pct"),
    ]
    
    for display_name, key in fields:
        row = _add_value_row(ws, row, display_name, returns.get(key))
    
    # Add sensitivity table
    row += 2
    sensitivity = export_data.get("sensitivity")
    if sensitivity:
        row = _add_sensitivity_table(ws, row, sensitivity)


def _add_sensitivity_table(ws, start_row: int, sensitivity: dict) -> int:
    """Add the 3x3 sensitivity table to a worksheet."""
    row = start_row
    
    # Title
    cell = ws.cell(row=row, column=1, value="Sensitivity Analysis: Levered IRR (%) by Exit Cap Rate and Construction Cost")
    cell.font = FONT_SECTION
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    row += 2
    
    # Column headers (construction cost)
    cols = sensitivity.get("cols", ["-10%", "Base", "+10%"])
    ws.cell(row=row, column=1, value="").font = FONT_NORMAL
    for i, col_label in enumerate(cols, 2):
        cell = ws.cell(row=row, column=i, value=col_label)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        cell.border = THIN_BORDER
    row += 1
    
    # Row headers and values
    rows_labels = sensitivity.get("rows", ["4.75%", "5.25%", "5.75%"])
    values = sensitivity.get("values", [[None]*3]*3)
    colors = sensitivity.get("colors", [["neutral"]*3]*3)
    base_pos = sensitivity.get("base_position", [1, 1])
    
    for i, row_label in enumerate(rows_labels):
        # Row header (cap rate)
        cell = ws.cell(row=row, column=1, value=row_label)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="right")
        cell.border = THIN_BORDER
        
        # Values
        for j, val in enumerate(values[i]):
            cell = ws.cell(row=row, column=j+2, value=f"{val:.1f}%" if val else "—")
            cell.alignment = Alignment(horizontal="center")
            cell.border = THIN_BORDER
            
            # Color coding
            color = colors[i][j] if i < len(colors) and j < len(colors[i]) else "neutral"
            cell.fill = COLOR_FILLS.get(color, FILL_CALCULATED)
            
            # Bold the base case
            if i == base_pos[0] and j == base_pos[1]:
                cell.font = Font(bold=True)
        
        row += 1
    
    # Legend
    row += 1
    ws.cell(row=row, column=1, value="Legend:").font = FONT_NORMAL
    
    legend_items = [
        (FILL_GREEN, "Meets target IRR"),
        (FILL_YELLOW, "Within 200bps of target"),
        (FILL_RED, "Below target"),
    ]
    
    col = 2
    for fill, label in legend_items:
        cell = ws.cell(row=row, column=col, value=label)
        cell.fill = fill
        cell.font = FONT_NORMAL
        cell.border = THIN_BORDER
        col += 1
    
    return row + 2


def _build_assumptions_sheet(wb: Workbook, export_data: dict):
    """Build the Assumptions & Sources sheet."""
    ws = wb.create_sheet("Assumptions & Sources")
    _set_column_widths(ws)
    
    pro_forma = export_data.get("pro_forma", {})
    
    row = 1
    row = _add_header_row(ws, row, ["Assumption", "Value", "Unit", "Label", "Source"])
    
    # Collect all estimated assumptions
    sections = [
        ("REVENUE ASSUMPTIONS", "revenue_assumptions"),
        ("COST ASSUMPTIONS", "cost_assumptions"),
        ("FINANCING ASSUMPTIONS", "financing_assumptions"),
        ("RETURN ASSUMPTIONS", "return_metrics"),
    ]
    
    for section_title, section_key in sections:
        section_data = pro_forma.get(section_key, {})
        
        # Check if section has any estimated fields
        estimated_fields = [
            (k, v) for k, v in section_data.items()
            if isinstance(v, dict) and v.get("label") == "estimated"
        ]
        
        if estimated_fields:
            row = _add_section_header(ws, row, section_title)
            
            for key, field in estimated_fields:
                display_name = key.replace("_", " ").title()
                row = _add_value_row(ws, row, display_name, field)
    
    # Add verification note
    row += 2
    note = "NOTE: All 'estimated' assumptions are sourced from market data and should be verified with your local broker before finalizing the underwrite."
    cell = ws.cell(row=row, column=1, value=note)
    cell.font = Font(italic=True, size=10)
    cell.fill = FILL_YELLOW
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)


# ═══════════════════════════════════════════════════════════════════════════════
# Main Export Function
# ═══════════════════════════════════════════════════════════════════════════════

def export_pro_forma(export_data: dict, deal_name: str = "Pro Forma") -> bytes:
    """
    Export a pro forma to an Excel workbook.
    
    Args:
        export_data: Dict containing 'pro_forma', 'sensitivity', 'warnings', etc.
        deal_name: Name for the deal (used in filename suggestion).
    
    Returns:
        Excel workbook as bytes (ready for Streamlit download).
    """
    wb = Workbook()
    
    # Build all sheets
    _build_summary_sheet(wb, export_data)
    _build_revenue_sheet(wb, export_data)
    _build_costs_sheet(wb, export_data)
    _build_financing_sheet(wb, export_data)
    _build_returns_sheet(wb, export_data)
    _build_assumptions_sheet(wb, export_data)
    
    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output.getvalue()


def get_suggested_filename(export_data: dict) -> str:
    """Generate a suggested filename for the export."""
    pro_forma = export_data.get("pro_forma", {})
    summary = pro_forma.get("project_summary", {})
    
    deal_name = summary.get("deal_name", "Pro_Forma")
    # Clean up for filename
    clean_name = deal_name.replace(" ", "_").replace("/", "-")
    
    return f"{clean_name}.xlsx"
