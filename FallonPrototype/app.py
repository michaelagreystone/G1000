"""
Fallon Financial Model — Streamlit UI (Phase 6)

A clean single-page interface for generating development pro formas
and answering contract/deal structure questions.
"""

import streamlit as st
import pandas as pd
import subprocess
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from FallonPrototype.agents.financial_agent import (
    run,
    extract_parameters,
    normalize_parameters,
    merge_clarification,
    check_missing_parameters,
    format_clarification_message,
    ProjectParameters,
    AgentResponse,
    retrieve_deal_comps,
    get_defaults_for_params,
    retrieve_defaults_context,
    format_financial_context,
    generate_pro_forma,
    validate_pro_forma,
)
from FallonPrototype.agents.contract_agent import answer_contract_question
from FallonPrototype.shared.vector_store import get_collection_counts
from FallonPrototype.shared.return_calculator import (
    compute_returns,
    check_return_discrepancy,
    compute_sensitivity_table,
    _val,
)
from FallonPrototype.shared.excel_export import export_pro_forma, get_suggested_filename


# ═══════════════════════════════════════════════════════════════════════════════
# Page Config
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Fallon Financial Model",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .warning-banner {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    .error-banner {
        background-color: #f8d7da;
        border: 1px solid #dc3545;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    .success-banner {
        background-color: #d4edda;
        border: 1px solid #28a745;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Session State Initialization
# ═══════════════════════════════════════════════════════════════════════════════

if "response" not in st.session_state:
    st.session_state.response = None
if "params" not in st.session_state:
    st.session_state.params = None
if "original_query" not in st.session_state:
    st.session_state.original_query = ""
if "needs_clarification" not in st.session_state:
    st.session_state.needs_clarification = False
if "adjusted_pro_forma" not in st.session_state:
    st.session_state.adjusted_pro_forma = None
if "contract_response" not in st.session_state:
    st.session_state.contract_response = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Pro Forma Generator"


# ═══════════════════════════════════════════════════════════════════════════════
# Sidebar — Status Panel
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("Fallon Financial Model")
    st.markdown("---")
    
    # Collection status
    st.subheader("Data Status")
    try:
        counts = get_collection_counts()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Deal Memos", counts.get("fallon_deal_data", 0))
        with col2:
            st.metric("Market Defaults", counts.get("fallon_market_defaults", 0))
    except Exception as e:
        st.warning(f"Could not load collection counts: {e}")
    
    st.markdown("---")
    
    # Re-index button
    if st.button("Re-index Data", use_container_width=True):
        with st.spinner("Running ingestion pipeline..."):
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "FallonPrototype.Financial Model.shared.run_all_ingestion"],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                )
                if result.returncode == 0:
                    st.success("Data re-indexed successfully!")
                else:
                    st.error(f"Ingestion failed: {result.stderr[:200]}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Clear session button
    if st.button("Clear Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    st.caption("Built for The Fallon Company")


# ═══════════════════════════════════════════════════════════════════════════════
# Main Area — Mode Selection
# ═══════════════════════════════════════════════════════════════════════════════

main_tab1, main_tab2 = st.tabs(["Pro Forma Generator", "Contract Q&A"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: Pro Forma Generator
# ═══════════════════════════════════════════════════════════════════════════════

with main_tab1:
    st.header("Development Pro Forma Generator")
    
    # Query input
    query = st.text_area(
        "Describe your project:",
        placeholder="""Examples:
    * "200-unit multifamily in Charlotte, targeting 15% IRR"
    * "Mixed-use hotel and apartments in Nashville, 300 keys and 180 units"
    * "80,000sf Class A office in Boston Seaport"
    * "150 condos in Charlotte with $12M land cost"
    """,
        height=120,
        key="query_input",
    )

# Generate button
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    generate_clicked = st.button("Generate Model", type="primary", use_container_width=True)

# Handle generation
if generate_clicked and query.strip():
    st.session_state.original_query = query
    
    with st.spinner("Building your pro forma..."):
        try:
            response = run(query)
            st.session_state.response = response
            st.session_state.needs_clarification = response.needs_clarification
            
            if response.needs_clarification:
                # Extract params for later merge
                params = normalize_parameters(extract_parameters(query))
                st.session_state.params = params
        except Exception as e:
            st.error(f"Error generating model: {e}")
            import traceback
            st.code(traceback.format_exc())


# ═══════════════════════════════════════════════════════════════════════════════
# Clarification Flow
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.needs_clarification and st.session_state.response:
    st.warning(st.session_state.response.answer)
    
    clarification = st.text_input("Your answer:", key="clarification_input")
    
    if st.button("Submit Clarification"):
        if clarification.strip():
            with st.spinner("Updating model with your details..."):
                try:
                    # Merge clarification with original params
                    merged_params = merge_clarification(
                        st.session_state.params,
                        clarification
                    )
                    
                    # Check if we have enough now
                    missing = check_missing_parameters(merged_params)
                    
                    if missing:
                        st.warning(format_clarification_message(missing))
                    else:
                        # Generate with merged params
                        deal_comps = retrieve_deal_comps(merged_params)
                        defaults_dict = get_defaults_for_params(merged_params)
                        defaults_chunks = retrieve_defaults_context(merged_params)
                        context = format_financial_context(
                            deal_comps, defaults_dict, defaults_chunks, merged_params
                        )
                        
                        pro_forma = generate_pro_forma(merged_params, context)
                        
                        if pro_forma:
                            calc_results = compute_returns(pro_forma)
                            warnings = check_return_discrepancy(pro_forma, calc_results)
                            
                            # Build response
                            response = AgentResponse(
                                intent="FINANCIAL_MODEL",
                                answer="Pro forma generated successfully.",
                                sources=[c["metadata"]["source"] for c in deal_comps],
                                raw_chunks=deal_comps,
                                confidence="medium",
                                export_data={
                                    "pro_forma": pro_forma,
                                    "calc_results": calc_results,
                                    "warnings": warnings,
                                },
                                warnings=warnings,
                            )
                            
                            st.session_state.response = response
                            st.session_state.needs_clarification = False
                            st.rerun()
                        else:
                            st.error("Could not generate pro forma. Please try again.")
                except Exception as e:
                    st.error(f"Error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Results Display
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.response and not st.session_state.needs_clarification:
    response = st.session_state.response
    export_data = response.export_data
    
    if export_data and "pro_forma" in export_data:
        pro_forma = st.session_state.adjusted_pro_forma or export_data["pro_forma"]
        calc_results = export_data.get("calc_results", {})
        warnings = export_data.get("warnings", [])
        
        st.markdown("---")
        
        # ═══════════════════════════════════════════════════════════════════════
        # Headline Metrics
        # ═══════════════════════════════════════════════════════════════════════
        
        returns = pro_forma.get("return_metrics", {})
        costs = pro_forma.get("cost_assumptions", {})
        summary = pro_forma.get("project_summary", {})
        
        deal_name = summary.get("deal_name", "Development Pro Forma")
        st.subheader(deal_name)
        
        # Four metric cards
        col1, col2, col3, col4 = st.columns(4)
        
        irr = _val(returns, "project_irr_levered_pct")
        calc_irr = calc_results.get("calc_irr_approx_pct")
        irr_delta = f"{calc_irr - irr:+.1f}%" if (irr and calc_irr) else None
        
        multiple = _val(returns, "equity_multiple_lp")
        calc_mult = calc_results.get("calc_equity_multiple_approx")
        mult_delta = f"{calc_mult - multiple:+.2f}x" if (multiple and calc_mult) else None
        
        poc = _val(returns, "profit_on_cost_pct")
        calc_poc = calc_results.get("calc_profit_on_cost_pct")
        poc_delta = f"{calc_poc - poc:+.1f}%" if (poc and calc_poc) else None
        
        total_cost = _val(costs, "total_project_cost")
        
        with col1:
            st.metric(
                "LP IRR",
                f"{irr:.1f}%" if irr else "—",
                delta=irr_delta,
                delta_color="normal" if irr_delta else "off",
            )
        
        with col2:
            st.metric(
                "Equity Multiple",
                f"{multiple:.2f}x" if multiple else "—",
                delta=mult_delta,
                delta_color="normal" if mult_delta else "off",
            )
        
        with col3:
            st.metric(
                "Profit on Cost",
                f"{poc:.1f}%" if poc else "—",
                delta=poc_delta,
                delta_color="normal" if poc_delta else "off",
            )
        
        with col4:
            st.metric(
                "Total Project Cost",
                f"${total_cost/1_000_000:.1f}M" if total_cost else "—",
            )
        
        # ═══════════════════════════════════════════════════════════════════════
        # Confidence & Warning Banners
        # ═══════════════════════════════════════════════════════════════════════
        
        if response.confidence == "low":
            st.error("**Low confidence:** No market-specific data found. All assumptions are national averages. Verify before use.")
        elif response.confidence == "medium":
            st.warning("**Medium confidence:** Market defaults used. Confirm rent and cost assumptions with local broker.")
        
        for warning in warnings:
            st.warning(warning)
        
        # ═══════════════════════════════════════════════════════════════════════
        # Pro Forma Tabs
        # ═══════════════════════════════════════════════════════════════════════
        
        st.markdown("---")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Summary", "Revenue", "Costs", "Financing", "Returns"
        ])
        
        def section_to_df(section: dict) -> pd.DataFrame:
            """Convert a pro forma section to a styled DataFrame."""
            rows = []
            for key, field in section.items():
                if isinstance(field, dict) and "value" in field:
                    rows.append({
                        "Variable": key.replace("_", " ").title(),
                        "Value": field.get("value"),
                        "Unit": field.get("unit", ""),
                        "Status": field.get("label", ""),
                    })
                elif field is not None and not isinstance(field, dict):
                    rows.append({
                        "Variable": key.replace("_", " ").title(),
                        "Value": field,
                        "Unit": "",
                        "Status": "confirmed",
                    })
            return pd.DataFrame(rows)
        
        def style_by_label(row):
            """Apply background color based on label."""
            label = row.get("Status", "")
            colors = {
                "confirmed": "background-color: #FFFF99",
                "estimated": "background-color: #CCE5FF",
                "calculated": "background-color: #FFFFFF",
                "missing": "background-color: #FFCCCC",
            }
            color = colors.get(label, "")
            return [color] * len(row)
        
        with tab1:
            df = section_to_df(pro_forma.get("project_summary", {}))
            st.dataframe(df.style.apply(style_by_label, axis=1), use_container_width=True, hide_index=True)
        
        with tab2:
            df = section_to_df(pro_forma.get("revenue_assumptions", {}))
            st.dataframe(df.style.apply(style_by_label, axis=1), use_container_width=True, hide_index=True)
        
        with tab3:
            df = section_to_df(pro_forma.get("cost_assumptions", {}))
            st.dataframe(df.style.apply(style_by_label, axis=1), use_container_width=True, hide_index=True)
        
        with tab4:
            df = section_to_df(pro_forma.get("financing_assumptions", {}))
            st.dataframe(df.style.apply(style_by_label, axis=1), use_container_width=True, hide_index=True)
        
        with tab5:
            df = section_to_df(pro_forma.get("return_metrics", {}))
            st.dataframe(df.style.apply(style_by_label, axis=1), use_container_width=True, hide_index=True)
        
        # ═══════════════════════════════════════════════════════════════════════
        # Sensitivity Table
        # ═══════════════════════════════════════════════════════════════════════
        
        st.markdown("---")
        st.subheader("Sensitivity Analysis: Levered IRR (%)")
        st.caption("Exit Cap Rate vs Construction Cost")
        
        target_irr = _val(returns, "lp_irr_pct", 14.0)
        sensitivity = compute_sensitivity_table(pro_forma, target_irr=target_irr)
        
        # Build sensitivity DataFrame
        sens_data = {}
        sens_data["Cap Rate"] = sensitivity["rows"]
        for i, col_label in enumerate(sensitivity["cols"]):
            sens_data[col_label] = [
                f"{sensitivity['values'][j][i]:.1f}%" if sensitivity['values'][j][i] else "—"
                for j in range(3)
            ]
        
        sens_df = pd.DataFrame(sens_data)
        
        def style_sensitivity(val):
            """Apply green/yellow/red styling to sensitivity cells."""
            if val == "—" or "%" not in str(val):
                return ""
            try:
                irr_val = float(val.replace("%", ""))
                if irr_val >= target_irr:
                    return "background-color: #C6EFCE"  # Green
                elif irr_val >= target_irr - 2:
                    return "background-color: #FFEB9C"  # Yellow
                else:
                    return "background-color: #FFC7CE"  # Red
            except:
                return ""
        
        styled_sens = sens_df.style.applymap(
            style_sensitivity,
            subset=["-10%", "Base", "+10%"]
        )
        
        st.dataframe(styled_sens, use_container_width=True, hide_index=True)
        
        # Legend
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("🟢 Meets target IRR")
        with col2:
            st.markdown("🟡 Within 200bps of target")
        with col3:
            st.markdown("🔴 Below target")
        
        # ═══════════════════════════════════════════════════════════════════════
        # Source Expander
        # ═══════════════════════════════════════════════════════════════════════
        
        with st.expander("View Assumption Sources & Comparable Deals"):
            st.subheader("Estimated Assumptions")
            
            # Collect estimated assumptions
            estimated = []
            for section_name in ["revenue_assumptions", "cost_assumptions", 
                                "financing_assumptions", "return_metrics"]:
                section = pro_forma.get(section_name, {})
                for key, field in section.items():
                    if isinstance(field, dict) and field.get("label") == "estimated":
                        estimated.append({
                            "Variable": key.replace("_", " ").title(),
                            "Value": field.get("value"),
                            "Source": field.get("source", ""),
                        })
            
            if estimated:
                st.dataframe(pd.DataFrame(estimated), use_container_width=True, hide_index=True)
            else:
                st.info("No estimated assumptions found.")
            
            st.subheader("Comparable Deals Retrieved")
            
            if response.raw_chunks:
                for i, chunk in enumerate(response.raw_chunks, 1):
                    st.markdown(f"**{i}. {chunk['metadata'].get('source', 'Unknown')}** — Relevance: {chunk.get('relevance', 'N/A')}")
                    st.caption(chunk.get("text", "")[:200] + "...")
            else:
                st.info("No comparable deals retrieved.")
        
        # ═══════════════════════════════════════════════════════════════════════
        # Adjust Assumptions Panel
        # ═══════════════════════════════════════════════════════════════════════
        
        with st.expander("Adjust Key Assumptions"):
            st.caption("Modify values below and click 'Update Returns' to recalculate without a new API call.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                adj_cap_rate = st.number_input(
                    "Exit Cap Rate (%)",
                    value=_val(returns, "exit_cap_rate_pct", 5.25),
                    min_value=3.0,
                    max_value=12.0,
                    step=0.25,
                    key="adj_cap_rate",
                )
                
                adj_hard_cost = st.number_input(
                    "Construction Cost ($/sf)",
                    value=_val(pro_forma.get("cost_assumptions", {}), "hard_cost_psf", 300),
                    min_value=100,
                    max_value=600,
                    step=10,
                    key="adj_hard_cost",
                )
                
                adj_rent = st.number_input(
                    "Monthly Rent ($/sf)",
                    value=_val(pro_forma.get("revenue_assumptions", {}), "rent_psf_monthly", 1.85),
                    min_value=0.5,
                    max_value=5.0,
                    step=0.05,
                    key="adj_rent",
                )
            
            with col2:
                adj_loan_rate = st.number_input(
                    "Construction Loan Rate (%)",
                    value=_val(pro_forma.get("financing_assumptions", {}), "construction_loan_rate_pct", 7.5),
                    min_value=4.0,
                    max_value=12.0,
                    step=0.25,
                    key="adj_loan_rate",
                )
                
                adj_lease_up = st.number_input(
                    "Lease-Up Months",
                    value=int(_val(pro_forma.get("revenue_assumptions", {}), "lease_up_months", 18)),
                    min_value=6,
                    max_value=36,
                    step=1,
                    key="adj_lease_up",
                )
            
            if st.button("Update Returns", type="secondary"):
                # Create adjusted pro forma
                import copy
                adjusted = copy.deepcopy(pro_forma)
                
                # Update values
                if "return_metrics" in adjusted and "exit_cap_rate_pct" in adjusted["return_metrics"]:
                    adjusted["return_metrics"]["exit_cap_rate_pct"]["value"] = adj_cap_rate
                
                if "cost_assumptions" in adjusted and "hard_cost_psf" in adjusted["cost_assumptions"]:
                    adjusted["cost_assumptions"]["hard_cost_psf"]["value"] = adj_hard_cost
                
                if "revenue_assumptions" in adjusted and "rent_psf_monthly" in adjusted["revenue_assumptions"]:
                    adjusted["revenue_assumptions"]["rent_psf_monthly"]["value"] = adj_rent
                
                if "financing_assumptions" in adjusted and "construction_loan_rate_pct" in adjusted["financing_assumptions"]:
                    adjusted["financing_assumptions"]["construction_loan_rate_pct"]["value"] = adj_loan_rate
                
                if "revenue_assumptions" in adjusted and "lease_up_months" in adjusted["revenue_assumptions"]:
                    adjusted["revenue_assumptions"]["lease_up_months"]["value"] = adj_lease_up
                
                # Recalculate returns
                new_calc = compute_returns(adjusted)
                
                # Update session state
                st.session_state.adjusted_pro_forma = adjusted
                response.export_data["calc_results"] = new_calc
                
                st.success("Returns updated! Scroll up to see new metrics.")
                st.rerun()
        
        # ═══════════════════════════════════════════════════════════════════════
        # Download Button
        # ═══════════════════════════════════════════════════════════════════════
        
        st.markdown("---")
        
        # Prepare export data with sensitivity
        export_data_with_sens = export_data.copy()
        export_data_with_sens["sensitivity"] = sensitivity
        if st.session_state.adjusted_pro_forma:
            export_data_with_sens["pro_forma"] = st.session_state.adjusted_pro_forma
        
        excel_bytes = export_pro_forma(export_data_with_sens, deal_name)
        filename = get_suggested_filename(export_data_with_sens)
        
        st.download_button(
            label="Download Model (.xlsx)",
            data=excel_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    
    else:
        # No pro forma in response — show the answer text
        st.info(response.answer)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: Contract Q&A
# ═══════════════════════════════════════════════════════════════════════════════

with main_tab2:
    st.header("Contract & Deal Structure Q&A")
    st.caption("Ask questions about JV agreements, waterfall structures, lease terms, and more.")
    
    # Sample questions
    with st.expander("Example Questions"):
        st.markdown("""
        - How does a typical waterfall distribution work?
        - What is a standard LP preferred return?
        - Explain the GP catch-up provision
        - What are typical promote structures for development deals?
        - What's the difference between cumulative and non-cumulative preferred returns?
        - How do tiered promotes work in institutional JVs?
        - What are standard construction contract provisions?
        - Explain NNN vs gross lease structures
        """)
    
    # Question input
    contract_question = st.text_area(
        "Your question:",
        placeholder="e.g., How does a 90/10 JV waterfall with 8% preferred return work?",
        height=100,
        key="contract_question",
    )
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        ask_clicked = st.button("Ask Question", type="primary", use_container_width=True, key="ask_contract")
    
    if ask_clicked and contract_question.strip():
        with st.spinner("Searching documents and generating answer..."):
            try:
                contract_response = answer_contract_question(contract_question)
                st.session_state.contract_response = contract_response
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Display contract response
    if st.session_state.contract_response:
        resp = st.session_state.contract_response
        
        # Confidence indicator
        confidence_colors = {"high": "green", "medium": "orange", "low": "red"}
        st.markdown(f"**Confidence:** :{confidence_colors.get(resp.confidence, 'gray')}[{resp.confidence.upper()}]")
        
        # Sources
        if resp.sources:
            st.caption(f"Sources: {', '.join(resp.sources)}")
        
        st.markdown("---")
        
        # Answer
        st.markdown(resp.answer)
        
        # Show retrieved chunks
        with st.expander("View Source Documents"):
            for i, chunk in enumerate(resp.chunks_used, 1):
                source = chunk.get("metadata", {}).get("source", "Unknown")
                relevance = chunk.get("relevance", "unknown")
                text = chunk.get("text", "")[:500]
                
                st.markdown(f"**Document {i}: {source}** (Relevance: {relevance})")
                st.text(text + "..." if len(chunk.get("text", "")) > 500 else text)
                st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# Footer
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.caption("Fallon Financial Model Generator | All assumptions require broker verification before use.")
