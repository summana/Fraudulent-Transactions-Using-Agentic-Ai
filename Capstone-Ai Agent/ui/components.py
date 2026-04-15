"""Reusable Streamlit UI components for the Fraud Detection Dashboard."""

import streamlit as st


def render_risk_badge(classification: str) -> None:
    """Render a color-coded pill badge for the risk classification."""
    color_map = {
        "Legitimate": "#28a745",
        "Suspicious": "#fd7e14",
        "Likely Fraud": "#dc3545",
    }
    color = color_map.get(classification, "#6c757d")
    st.markdown(
        f'<span style="background-color:{color};color:#fff;padding:4px 14px;'
        f'border-radius:20px;font-size:0.85rem;font-weight:600;">'
        f"{classification}</span>",
        unsafe_allow_html=True,
    )


def render_risk_score_bar(score: int, max_score: int = 50) -> None:
    """Render a risk score with a progress bar."""
    pct = min(score / max_score, 1.0)
    if pct <= 0.2:
        label_color = "#28a745"
    elif pct <= 0.5:
        label_color = "#fd7e14"
    else:
        label_color = "#dc3545"
    st.markdown(
        f'<span style="font-size:1.1rem;font-weight:700;color:{label_color};">'
        f"Risk Score: {score} / {max_score}</span>",
        unsafe_allow_html=True,
    )
    st.progress(pct)


def render_triggered_rules(rules_list: list) -> None:
    """Render triggered rules as colored pill tags."""
    if not rules_list:
        st.markdown(
            '<span style="background-color:#28a745;color:#fff;padding:4px 12px;'
            'border-radius:16px;font-size:0.8rem;">&#10003; No rules triggered</span>',
            unsafe_allow_html=True,
        )
        return

    pills_html = " ".join(
        f'<span style="background-color:#e74c3c;color:#fff;padding:4px 10px;'
        f'border-radius:16px;font-size:0.78rem;margin:2px 4px 2px 0;'
        f'display:inline-block;">'
        f'<b>{r["rule_id"]}</b>: {r["description"]}</span>'
        for r in rules_list
    )
    st.markdown(pills_html, unsafe_allow_html=True)


def render_explanation_box(reasoning: str) -> None:
    """Render the LLM reasoning in a styled info box."""
    st.info(reasoning)


def render_transaction_card(result: dict) -> None:
    """Minimal transaction analysis card."""
    st.markdown("---")
    st.write(f"Transaction ID: {result.get('transaction_id', 'N/A')}")
    st.write(f"Classification: {result.get('classification', 'N/A')}")
    st.write(f"Reasoning: {result.get('reasoning', 'No reasoning available.')}")
