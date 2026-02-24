"""
Return Metrics Calculator (Phase 4.4)

Pure Python calculator for cross-checking Claude's return estimates.
Runs the same assumptions as a simplified DCF to validate the model.
"""


def _val(section: dict, key: str, default=None):
    """
    Safely extract the 'value' from a pro forma field.
    
    Args:
        section: A section dict from the pro forma.
        key: The field name to extract.
        default: Default value if field is missing or non-numeric.
    
    Returns:
        The numeric value, or default if not available.
    """
    if not isinstance(section, dict):
        return default
    
    field = section.get(key)
    
    if field is None:
        return default
    
    if isinstance(field, dict):
        val = field.get("value")
        if val is None:
            return default
        try:
            return float(val)
        except (TypeError, ValueError):
            return default
    
    try:
        return float(field)
    except (TypeError, ValueError):
        return default


def _estimate_noi(revenue: dict, summary: dict) -> float | None:
    """
    Estimate stabilized NOI from revenue assumptions.
    
    Simplified calculation based on program type.
    """
    program_type = summary.get("program_type", "multifamily")
    
    if program_type in ("multifamily", "condo"):
        # Multifamily: rent_psf * total_sf * 12 * occupancy + other_income
        rent_psf = _val(revenue, "rent_psf_monthly")
        occupancy = _val(revenue, "stabilized_occupancy_pct", 93) / 100
        unit_count = _val(summary, "unit_count")
        avg_unit_sf = 900  # Default average
        
        if rent_psf and unit_count:
            total_sf = unit_count * avg_unit_sf
            gross_rent = rent_psf * total_sf * 12
            other_income = _val(revenue, "other_income_per_unit_monthly", 125) * unit_count * 12
            egi = (gross_rent + other_income) * occupancy
            # Assume 35% operating expense ratio
            noi = egi * 0.65
            return noi
    
    elif program_type == "office":
        # Office: rent_psf_annual * rentable_sf * occupancy
        rent_psf = _val(revenue, "rent_psf_annual_nnn")
        rentable_sf = _val(summary, "rentable_sf")
        occupancy = _val(revenue, "stabilized_occupancy_pct", 88) / 100
        
        if rent_psf and rentable_sf:
            # NNN rent is basically NOI for office
            noi = rent_psf * rentable_sf * occupancy
            return noi
    
    elif program_type == "hotel":
        # Hotel: RevPAR * keys * 365 * margin
        adr = _val(revenue, "adr")
        occupancy = _val(revenue, "stabilized_occupancy_pct", 70) / 100
        keys = _val(summary, "total_keys")
        
        if adr and keys:
            revpar = adr * occupancy
            gross_revenue = revpar * keys * 365
            # Hotel NOI margin typically 30-40%
            noi = gross_revenue * 0.35
            return noi
    
    return None


def compute_returns(pro_forma: dict) -> dict:
    """
    Compute return metrics from a pro forma using pure Python math.
    
    Args:
        pro_forma: The generated pro forma dict.
    
    Returns:
        Dict with calculated return metrics for comparison.
    """
    costs = pro_forma.get("cost_assumptions", {})
    financing = pro_forma.get("financing_assumptions", {})
    revenue = pro_forma.get("revenue_assumptions", {})
    summary = pro_forma.get("project_summary", {})
    returns = pro_forma.get("return_metrics", {})
    
    total_cost = _val(costs, "total_project_cost")
    equity = _val(financing, "equity_required")
    lp_equity = _val(financing, "lp_equity_amount")
    
    # Get or estimate NOI
    noi = _val(returns, "stabilized_noi")
    if noi is None:
        noi = _estimate_noi(revenue, summary)
    
    # Exit cap rate
    cap_rate = _val(returns, "exit_cap_rate_pct", 5.25) / 100
    
    # Calculate exit value
    gross_exit = noi / cap_rate if (noi and cap_rate > 0) else None
    
    # Profit calculations
    sale_costs = gross_exit * 0.025 if gross_exit else None
    net_exit = gross_exit - sale_costs if gross_exit else None
    total_profit = net_exit - total_cost if (net_exit and total_cost) else None
    
    # Profit on cost
    profit_on_cost = (total_profit / total_cost * 100) if (total_profit and total_cost) else None
    
    # Simplified IRR approximation
    construction_months = _val(summary, "construction_duration_months", 18)
    lease_up_months = _val(revenue, "lease_up_months", 18)
    exit_year = _val(returns, "exit_year", 5)
    
    hold_years = exit_year if exit_year else (construction_months + lease_up_months) / 12 + 2
    
    equity_multiple = None
    irr_approx = None
    
    if lp_equity and lp_equity > 0 and total_profit and equity:
        # LP share of profit (assuming 90/10 split with 8% pref and 20% promote)
        lp_pct = _val(financing, "lp_equity_pct", 90) / 100
        pref_return = _val(financing, "preferred_return_pct", 8) if "preferred_return_pct" in financing else 8
        
        # Simple LP return calc
        lp_profit_share = total_profit * lp_pct * 0.8  # After GP promote
        lp_total_return = lp_equity + lp_profit_share
        
        equity_multiple = lp_total_return / lp_equity if lp_equity > 0 else None
        
        # Approximate IRR: (multiple ^ (1/years)) - 1
        if equity_multiple and equity_multiple > 0 and hold_years > 0:
            try:
                irr_approx = ((equity_multiple ** (1 / hold_years)) - 1) * 100
            except (ValueError, ZeroDivisionError, TypeError):
                irr_approx = None
        elif equity_multiple and equity_multiple <= 0:
            # Negative or zero multiple means loss - return negative IRR
            irr_approx = -100.0  # Total loss indicator
    
    return {
        "calc_noi": noi,
        "calc_gross_exit_value": gross_exit,
        "calc_net_exit_value": net_exit,
        "calc_total_profit": total_profit,
        "calc_profit_on_cost_pct": profit_on_cost,
        "calc_equity_multiple_approx": equity_multiple,
        "calc_irr_approx_pct": irr_approx,
        "calc_hold_years": hold_years,
    }


def check_return_discrepancy(pro_forma: dict, calc_results: dict) -> list[str]:
    """
    Compare Claude's return estimates with calculator results.
    
    Flags discrepancies greater than 15%.
    
    Args:
        pro_forma: The generated pro forma dict.
        calc_results: Results from compute_returns().
    
    Returns:
        List of warning strings for significant discrepancies.
    """
    warnings = []
    returns = pro_forma.get("return_metrics", {})
    
    # Compare profit on cost
    claude_poc = _val(returns, "profit_on_cost_pct")
    calc_poc = calc_results.get("calc_profit_on_cost_pct")
    
    if claude_poc and calc_poc:
        diff = abs(claude_poc - calc_poc) / calc_poc * 100 if calc_poc != 0 else 0
        if diff > 15:
            warnings.append(
                f"Profit on cost discrepancy: model shows {claude_poc:.1f}%, "
                f"calculator estimates {calc_poc:.1f}%. Review cost or exit assumptions."
            )
    
    # Compare equity multiple
    claude_mult = _val(returns, "equity_multiple_lp")
    calc_mult = calc_results.get("calc_equity_multiple_approx")
    
    if claude_mult and calc_mult:
        diff = abs(claude_mult - calc_mult) / calc_mult * 100 if calc_mult != 0 else 0
        if diff > 15:
            warnings.append(
                f"Equity multiple discrepancy: model shows {claude_mult:.2f}x, "
                f"calculator estimates {calc_mult:.2f}x. Review construction cost or exit cap rate."
            )
    
    # Compare IRR
    claude_irr = _val(returns, "project_irr_levered_pct")
    calc_irr = calc_results.get("calc_irr_approx_pct")
    
    if claude_irr and calc_irr:
        diff = abs(claude_irr - calc_irr) / calc_irr * 100 if calc_irr != 0 else 0
        if diff > 15:
            warnings.append(
                f"IRR discrepancy: model shows {claude_irr:.1f}%, "
                f"calculator estimates {calc_irr:.1f}%. Review timing or leverage assumptions."
            )
    
    return warnings


def compute_sensitivity_table(pro_forma: dict, target_irr: float | None = None) -> dict:
    """
    Compute a 3x3 sensitivity table for cap rate vs construction cost.
    
    Args:
        pro_forma: The generated pro forma dict.
        target_irr: LP target IRR for deal-works coloring (optional).
    
    Returns:
        Dict with row/col labels and IRR values for each scenario.
    """
    returns = pro_forma.get("return_metrics", {})
    costs = pro_forma.get("cost_assumptions", {})
    
    base_cap_rate = _val(returns, "exit_cap_rate_pct", 5.25)
    base_hard_cost = _val(costs, "hard_cost_psf", 300)
    
    # Define scenarios
    cap_rates = [base_cap_rate - 0.5, base_cap_rate, base_cap_rate + 0.5]
    cost_factors = [0.9, 1.0, 1.1]  # -10%, base, +10%
    
    values = []
    colors = []
    
    for cap_rate in cap_rates:
        row_values = []
        row_colors = []
        
        for cost_factor in cost_factors:
            # Create scenario pro forma
            scenario = _create_scenario(pro_forma, cap_rate, cost_factor)
            
            # Compute returns for scenario
            scenario_returns = compute_returns(scenario)
            irr = scenario_returns.get("calc_irr_approx_pct")
            
            # Handle None, complex, or invalid IRR values
            if irr is not None and isinstance(irr, (int, float)) and not isinstance(irr, complex):
                row_values.append(round(float(irr), 1))
            else:
                row_values.append(None)
            
            # Determine color based on target
            irr_for_color = row_values[-1]  # Use the cleaned value
            if target_irr and irr_for_color is not None:
                if irr_for_color >= target_irr:
                    row_colors.append("green")
                elif irr_for_color >= target_irr - 2:  # Within 200bps
                    row_colors.append("yellow")
                else:
                    row_colors.append("red")
            else:
                row_colors.append("neutral")
        
        values.append(row_values)
        colors.append(row_colors)
    
    return {
        "row_label": "Exit Cap Rate",
        "col_label": "Construction Cost",
        "rows": [f"{r:.2f}%" for r in cap_rates],
        "cols": ["-10%", "Base", "+10%"],
        "values": values,
        "colors": colors,
        "base_position": [1, 1],  # Center cell
    }


def _create_scenario(pro_forma: dict, cap_rate: float, cost_factor: float) -> dict:
    """Create a scenario copy of the pro forma with modified assumptions."""
    import copy
    scenario = copy.deepcopy(pro_forma)
    
    # Modify cap rate
    if "return_metrics" in scenario:
        if "exit_cap_rate_pct" in scenario["return_metrics"]:
            if isinstance(scenario["return_metrics"]["exit_cap_rate_pct"], dict):
                scenario["return_metrics"]["exit_cap_rate_pct"]["value"] = cap_rate
            else:
                scenario["return_metrics"]["exit_cap_rate_pct"] = cap_rate
    
    # Modify construction costs
    costs = scenario.get("cost_assumptions", {})
    
    for key in ["hard_cost_psf", "hard_cost_total", "soft_cost_total", 
                "contingency_total", "total_project_cost"]:
        if key in costs:
            if isinstance(costs[key], dict) and costs[key].get("value"):
                costs[key]["value"] *= cost_factor
            elif isinstance(costs[key], (int, float)):
                costs[key] *= cost_factor
    
    # Recalculate equity
    financing = scenario.get("financing_assumptions", {})
    total_cost = _val(costs, "total_project_cost")
    loan_amount = _val(financing, "construction_loan_amount")
    
    if total_cost and loan_amount:
        new_equity = total_cost - loan_amount
        if "equity_required" in financing:
            if isinstance(financing["equity_required"], dict):
                financing["equity_required"]["value"] = new_equity
        
        lp_pct = _val(financing, "lp_equity_pct", 90) / 100
        if "lp_equity_amount" in financing:
            if isinstance(financing["lp_equity_amount"], dict):
                financing["lp_equity_amount"]["value"] = new_equity * lp_pct
    
    return scenario
