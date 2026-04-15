

import json
import re
import urllib.request
import urllib.error

DISCLAIMER_TEXT = (
    "This is an AI-assisted analysis for decision support only. "
    "Final action must be reviewed and approved by an authorized human analyst."
)

# Hardcoded config for minimal version
OLLAMA_MODEL = "llama3.2:1b"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_API_KEY = ""
OLLAMA_TIMEOUT_SECONDS = 4.0


def build_llm_prompt(
    transaction: dict,
    triggered_rules: list,
    score: int,
    classification: str,
    data_issues: list[str],
) -> str:
    """Build the LLM prompt for fraud analysis.

    Args:
        transaction: Raw transaction data dict.
        triggered_rules: List of triggered rule dicts.
        score: Computed risk score.
        classification: Risk classification string.
        data_issues: List of data quality issue strings.

    Returns:
        The formatted prompt string.
    """
    rules_text = "\n".join(
        [
            f"- {r['rule_id']}: {r['description']} (Weight: {r['risk_weight']})"
            for r in triggered_rules
        ]
    )
    if not rules_text:
        rules_text = "None"

    data_issues_text = (
        "\n".join([f"- {issue}" for issue in data_issues])
        if data_issues
        else "- None"
    )

    prompt = f"""
Analyze the following banking transaction for potential fraud.

Transaction Details:
{json.dumps(transaction, indent=2)}

Triggered Rules:
{rules_text}

Data Quality Notes:
{data_issues_text}

Computed Risk Score: {score}
Initial Classification: {classification}

Task:
1. Write a 3-5 sentence human-readable reasoning summary using neutral, compliance-safe language.
2. Keep the reasoning audit-friendly: mention observed facts (rules, score, data quality notes) and avoid speculation.
3. Do not make definitive accusations. Do not guarantee fraud.
4. Suggest ONE next action from this exact list: [Monitor, Request Customer Verification, Escalate to Senior Analyst, Flag for Compliance Review]
5. Include the following exact disclaimer at the end: "{DISCLAIMER_TEXT}"

Output your response clearly with headings for "Reasoning Summary", "Recommended Action", and "Disclaimer".
"""
    return prompt





def parse_llm_sections(
    llm_response: str, classification: str
) -> tuple[str, str, str]:
    """Parse reasoning, action, and disclaimer from the LLM response text."""
    if not llm_response:
        llm_response = ""
    reasoning_match = re.search(
        r"(?:Reasoning(?:\s+Summary)?|Summary)\s*:\s*(.*?)"
        r"(?:\n\s*\n|\n\s*(?:Next\s*Action|Recommended\s*Action|Disclaimer)\s*:|$)",
        llm_response,
        flags=re.IGNORECASE | re.DOTALL,
    )
    action_match = re.search(
        r"(?:Next\s*Action|Recommended\s*Action)\s*:\s*(.*?)"
        r"(?:\n\s*\n|\n\s*Disclaimer\s*:|$)",
        llm_response,
        flags=re.IGNORECASE | re.DOTALL,
    )
    disclaimer_match = re.search(
        r"Disclaimer\s*:\s*(.*)$",
        llm_response,
        flags=re.IGNORECASE | re.DOTALL,
    )
    reasoning = ""
    action = ""
    disclaimer = ""
    if reasoning_match:
        reasoning = reasoning_match.group(1).strip()
    if action_match:
        action = action_match.group(1).strip()
    if disclaimer_match:
        disclaimer = disclaimer_match.group(1).strip()
    if not reasoning:
        reasoning = llm_response.strip() or "No reasoning summary returned by model."
    if not action:
        action = "Monitor"
    if not disclaimer:
        disclaimer = DISCLAIMER_TEXT
    return reasoning, action, disclaimer


def call_ollama(
    prompt: str,
    transaction: dict,
    triggered_rules: list,
    classification: str,
    data_issues: list[str],
) -> str:
    """Send a prompt to the Ollama API and return the response text. Minimal version."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 90,
        },
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **(
                {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
                if OLLAMA_API_KEY
                else {}
            ),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=OLLAMA_TIMEOUT_SECONDS
        ) as response:
            body = response.read().decode("utf-8", errors="replace")
        parsed = json.loads(body)
        text = str(parsed.get("response", "")).strip()
        if not text:
            raise RuntimeError("Ollama returned an empty response")
        return text
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}")
