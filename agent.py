import os
import re
import json
from datetime import datetime

import openai
import chromadb
from dotenv import load_dotenv

try:
    import phonenumbers
except Exception:
    phonenumbers = None


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Phase 2: primary conversion CTA for qualified leads.
BOOKING_LINK = (os.getenv("BOOKING_LINK") or "").strip()


# ----------------------------
# Deterministic verification signals (Phase 1)
# ----------------------------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email_format(email):
    email = (email or "").strip()
    if not email:
        return False
    if not EMAIL_RE.match(email):
        return False
    if ".." in email:
        return False
    return True


def validate_phone_us(phone_raw, default_region="US"):
    """
    Validate a US phone number and normalize to E.164.
    Returns (is_valid, e164_or_none).
    """
    phone_raw = (phone_raw or "").strip()
    if not phone_raw:
        return False, None
    if phonenumbers is None:
        return False, None

    try:
        parsed = phonenumbers.parse(phone_raw, default_region)
        if not phonenumbers.is_valid_number(parsed):
            return False, None

        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        digits = re.sub(r"\D", "", e164)

        # Reject obvious fake patterns.
        if digits in {"0000000000", "1234567890"}:
            return False, None
        if len(set(digits)) == 1:
            return False, None

        return True, e164
    except Exception:
        return False, None


def detect_obvious_fake_patterns(name, email, phone, text):
    name = (name or "").strip().lower()
    email = (email or "").strip().lower()
    phone = (phone or "").strip()
    text = (text or "").strip().lower()

    # Very short gibberish-ish names.
    if name in {"asdf", "aa"}:
        return True
    if name and len(name) <= 2:
        return True

    # Spammy tokens in chat.
    spam_tokens = ["$$$", "buy now", "click here"]
    if any(tok in text for tok in spam_tokens):
        return True

    return False


def required_fields_present(name, email, phone):
    name = (name or "").strip()
    email_ok = validate_email_format(email)
    phone_ok, _ = validate_phone_us(phone)
    return bool(name) and (email_ok or phone_ok)


def _compute_signals(session):
    lead = session.get("lead", {}) or {}
    name = lead.get("name", "")
    email = lead.get("email", "")
    phone = lead.get("phone", "")

    email_ok = validate_email_format(email)
    phone_ok, phone_e164 = validate_phone_us(phone)

    recent_text = " ".join(
        [m.get("content", "") for m in (session.get("messages", []) or [])[-6:]]
    )
    fake = detect_obvious_fake_patterns(name, email, phone, recent_text)

    signals = {
        "email_format_valid": bool(email_ok),
        "phone_valid_us": bool(phone_ok),
        "required_fields_present": bool(required_fields_present(name, email, phone)),
        "obvious_fake_patterns_detected": bool(fake),
    }
    return signals, phone_e164


# ----------------------------
# LLM verification (Phase 1)
# ----------------------------

VERIFICATION_SYSTEM_PROMPT = """You are LeadCraft AI's VERIFICATION engine.

Your only job is to evaluate DATA QUALITY, not sales readiness.
Do not qualify intent. Do not recommend pricing. Do not pitch.

You will be given:
- deterministic validation signals computed in code
- lead form data
- chat transcript

Important:
- You do NOT validate formats. You interpret the provided signals.
- You must return ONLY valid JSON matching the schema exactly. No extra keys. No markdown. No commentary.

Schema:
{
  "verification_status": "pass" | "needs_more_info" | "fail",
  "verification_score": 0-100,
  "reasons": [string],
  "risk_flags": ["spam" | "disposable_email" | "incoherent" | "contradictory" | "missing_contact" | "invalid_phone" | "invalid_email" | "suspicious_intent" | "other"],
  "missing_fields": [string],
  "required_followups": [string],
  "verified_fields": [string],
  "contact": {
    "email_valid": true | false,
    "phone_valid": true | false,
    "preferred_contact_method": "email" | "phone" | "either" | "unknown"
  }
}

Rules:
- "pass" means the lead appears real with usable contact info and coherent answers.
- "needs_more_info" means the lead might be real but key fields are missing/unclear; provide 1-3 targeted followups.
- "fail" means high likelihood of spam/fake info or unusable contact details.
- Treat phone as valid only if it appears to be a real phone number format with country code or clear national format AND not obviously fake (e.g., 1234567890, 0000000000).
- verification_score reflects confidence in data quality (not buying intent).
- Followups must be short, specific, and answerable in one message.

Few-shot examples:

Example 1 (PASS)
Input:
{
  "signals": {"email_format_valid": true, "phone_valid_us": true, "required_fields_present": true, "obvious_fake_patterns_detected": false},
  "lead_form": {"name": "Sarah Miller", "email": "sarah@millersolar.com", "phone": "+13125551234"},
  "chat_transcript": [{"role":"user","content":"We sell residential solar in Illinois. We need more qualified inbound leads and want to automate follow-up."}]
}
Output:
{
  "verification_status": "pass",
  "verification_score": 92,
  "reasons": ["Contact details appear usable and the conversation is coherent."],
  "risk_flags": [],
  "missing_fields": [],
  "required_followups": [],
  "verified_fields": ["name","email","phone"],
  "contact": {"email_valid": true, "phone_valid": true, "preferred_contact_method": "either"}
}

Example 2 (NEEDS_MORE_INFO - invalid phone)
Input:
{
  "signals": {"email_format_valid": true, "phone_valid_us": false, "required_fields_present": true, "obvious_fake_patterns_detected": true},
  "lead_form": {"name": "Mike", "email": "mike@gmail.com", "phone": "0000000000"},
  "chat_transcript": [{"role":"user","content":"Just looking around."}]
}
Output:
{
  "verification_status": "needs_more_info",
  "verification_score": 60,
  "reasons": ["Email looks usable, but the phone number appears invalid or fake."],
  "risk_flags": ["invalid_phone"],
  "missing_fields": ["phone"],
  "required_followups": ["What is your valid U.S. phone number?"],
  "verified_fields": ["name","email"],
  "contact": {"email_valid": true, "phone_valid": false, "preferred_contact_method": "email"}
}

Example 3 (FAIL - spam/gibberish)
Input:
{
  "signals": {"email_format_valid": false, "phone_valid_us": false, "required_fields_present": false, "obvious_fake_patterns_detected": true},
  "lead_form": {"name": "asdf", "email": "aaa@aaa", "phone": "1111111111"},
  "chat_transcript": [{"role":"user","content":"buy now cheap leads $$$ click here"}]
}
Output:
{
  "verification_status": "fail",
  "verification_score": 5,
  "reasons": ["Likely spam or fake information; contact details are not usable."],
  "risk_flags": ["spam","invalid_email","invalid_phone"],
  "missing_fields": ["name","email","phone"],
  "required_followups": ["Please provide your full name and a valid email or U.S. phone number."],
  "verified_fields": [],
  "contact": {"email_valid": false, "phone_valid": false, "preferred_contact_method": "unknown"}
}"""

QUALIFICATION_SYSTEM_PROMPT = """You are LeadCraft AI's QUALIFICATION engine.

Your only job is to assess INTENT and SALES READINESS after the lead has been VERIFIED.

Return ONLY valid JSON matching the schema exactly. No extra keys. No markdown. No commentary.

Schema:
{
  "qualification_status": "qualified" | "follow_up_later" | "unqualified",
  "intent_score": 0-100,
  "intent_bucket": "hot" | "warm" | "cold",
  "signals": [string],
  "deal_blockers": [string],
  "recommended_next_action": "book_call" | "follow_up" | "disqualify",
  "follow_up_window_days": 0-30,
  "one_best_followup_question": string
}

Rules:
- If qualified -> recommended_next_action MUST be "book_call"
- If follow_up_later -> recommended_next_action MUST be "follow_up" and include follow_up_window_days (use 7/14/30)
- If unqualified -> recommended_next_action MUST be "disqualify"
- Provide 3-7 short signals and 0-4 blockers.
- one_best_followup_question must move them closer to booking or confirm follow-up timing.
- Do not mention lead magnets. Do not offer guides. The primary CTA is booking a call.

Few-shot examples:

Example (HOT / qualified)
Input:
{
  "verification_summary": {"verification_status":"pass","risk_flags":[],"verified_fields":["name","email","phone"]},
  "lead_form": {"name":"Sarah Miller","email":"sarah@millersolar.com","phone":"+13125551234"},
  "chat_transcript": [{"role":"user","content":"We need to increase inbound leads this month. Can we book a call to see how this works?"}]
}
Output:
{
  "qualification_status":"qualified",
  "intent_score":90,
  "intent_bucket":"hot",
  "signals":["asked to book a call","clear business goal","near-term timeline"],
  "deal_blockers":[],
  "recommended_next_action":"book_call",
  "follow_up_window_days":0,
  "one_best_followup_question":"What time zone are you in?"
}

Example (WARM / follow_up_later)
Input:
{
  "verification_summary": {"verification_status":"pass","risk_flags":[],"verified_fields":["name","email","phone"]},
  "lead_form": {"name":"Mike","email":"mike@gmail.com","phone":"+14155551234"},
  "chat_transcript": [{"role":"user","content":"This seems interesting but I’m not ready to talk yet. Maybe later."}]
}
Output:
{
  "qualification_status":"follow_up_later",
  "intent_score":55,
  "intent_bucket":"warm",
  "signals":["expressed interest","not ready to talk now"],
  "deal_blockers":["timing not confirmed"],
  "recommended_next_action":"follow_up",
  "follow_up_window_days":14,
  "one_best_followup_question":"Is it okay if I follow up in about two weeks, and should I reach you by email or phone?"
}

"""


def _validate_verification_schema(obj):
    allowed_flags = {
        "spam",
        "disposable_email",
        "incoherent",
        "contradictory",
        "missing_contact",
        "invalid_phone",
        "invalid_email",
        "suspicious_intent",
        "other",
    }
    if not isinstance(obj, dict):
        return None
    expected = {
        "verification_status",
        "verification_score",
        "reasons",
        "risk_flags",
        "missing_fields",
        "required_followups",
        "verified_fields",
        "contact",
    }
    if set(obj.keys()) != expected:
        return None
    if obj.get("verification_status") not in {"pass", "needs_more_info", "fail"}:
        return None
    score = obj.get("verification_score")
    if not isinstance(score, int) or score < 0 or score > 100:
        return None
    for k in ["reasons", "risk_flags", "missing_fields", "required_followups", "verified_fields"]:
        if not isinstance(obj.get(k), list) or not all(isinstance(x, str) for x in obj[k]):
            return None
    if any(f not in allowed_flags for f in obj["risk_flags"]):
        return None
    contact = obj.get("contact")
    if not isinstance(contact, dict):
        return None
    if set(contact.keys()) != {"email_valid", "phone_valid", "preferred_contact_method"}:
        return None
    if not isinstance(contact.get("email_valid"), bool):
        return None
    if not isinstance(contact.get("phone_valid"), bool):
        return None
    if contact.get("preferred_contact_method") not in {"email", "phone", "either", "unknown"}:
        return None
    return obj


def _validate_qualification_schema(obj):
    if not isinstance(obj, dict):
        return None
    expected = {
        "qualification_status",
        "intent_score",
        "intent_bucket",
        "signals",
        "deal_blockers",
        "recommended_next_action",
        "follow_up_window_days",
        "one_best_followup_question",
    }
    if set(obj.keys()) != expected:
        return None
    if obj.get("qualification_status") not in {"qualified", "follow_up_later", "unqualified"}:
        return None
    score = obj.get("intent_score")
    if not isinstance(score, int) or score < 0 or score > 100:
        return None
    if obj.get("intent_bucket") not in {"hot", "warm", "cold"}:
        return None
    if not isinstance(obj.get("signals"), list) or not all(isinstance(x, str) for x in obj["signals"]):
        return None
    if not isinstance(obj.get("deal_blockers"), list) or not all(isinstance(x, str) for x in obj["deal_blockers"]):
        return None
    if obj.get("recommended_next_action") not in {"book_call", "follow_up", "disqualify"}:
        return None
    days = obj.get("follow_up_window_days")
    if not isinstance(days, int) or days < 0 or days > 30:
        return None
    if not isinstance(obj.get("one_best_followup_question"), str):
        return None

    # Rules enforcement
    qs = obj["qualification_status"]
    rna = obj["recommended_next_action"]
    if qs == "qualified" and rna != "book_call":
        return None
    if qs == "follow_up_later" and rna != "follow_up":
        return None
    if qs == "unqualified" and rna != "disqualify":
        return None
    if qs == "follow_up_later" and days not in {7, 14, 30}:
        return None
    if qs != "follow_up_later" and days != 0:
        return None
    return obj


def verify_lead_llm(session):
    signals, phone_e164 = _compute_signals(session)
    session["signals"] = signals

    lead = session.get("lead", {}) or {}
    lead_form = {
        "name": lead.get("name", ""),
        "email": lead.get("email", ""),
        "phone": lead.get("phone", ""),
        "company": lead.get("company", ""),
        "role": lead.get("role", ""),
        "preferred_contact_method": lead.get("preferred_contact_method", "unknown"),
    }
    transcript = (session.get("messages", []) or [])[-6:]

    model_input = {
        "signals": signals,
        "lead_form": lead_form,
        "chat_transcript": transcript,
    }

    # Default fallback if parsing fails.
    fallback = {
        "verification_status": "needs_more_info",
        "verification_score": 0,
        "reasons": ["Unable to verify data quality from the provided information."],
        "risk_flags": ["other"],
        "missing_fields": [],
        "required_followups": ["Please confirm your name and provide a valid email or U.S. phone number."],
        "verified_fields": [],
        "contact": {
            "email_valid": bool(signals["email_format_valid"]),
            "phone_valid": bool(signals["phone_valid_us"]),
            "preferred_contact_method": "unknown",
        },
    }

    try:
        resp = openai.ChatCompletion.create(
            model=os.getenv("VERIFICATION_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": VERIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(model_input, ensure_ascii=True)},
            ],
            temperature=0.0,
            max_tokens=500,
        )
        content = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(content)
        verified = _validate_verification_schema(parsed)
        if verified is None:
            session["verification"] = fallback
            return fallback, phone_e164

        def _add_unique(lst, item):
            if item and item not in lst:
                lst.append(item)

        # Deterministic enforcement:
        # If a contact field is provided but invalid, force needs_more_info (unless already fail).
        email_raw = (lead_form.get("email") or "").strip()
        phone_raw = (lead_form.get("phone") or "").strip()
        if email_raw and not signals["email_format_valid"]:
            if verified.get("verification_status") != "fail":
                verified["verification_status"] = "needs_more_info"
            _add_unique(verified["risk_flags"], "invalid_email")
            _add_unique(verified["missing_fields"], "email")
            _add_unique(verified["required_followups"], "What is your valid email address?")
        if phone_raw and not signals["phone_valid_us"]:
            if verified.get("verification_status") != "fail":
                verified["verification_status"] = "needs_more_info"
            _add_unique(verified["risk_flags"], "invalid_phone")
            _add_unique(verified["missing_fields"], "phone")
            _add_unique(verified["required_followups"], "What is your valid U.S. phone number?")

        # Deterministic gating: never allow "pass" unless required fields are present and no obvious fake.
        if not signals["required_fields_present"]:
            verified["verification_status"] = "needs_more_info"
        if signals["obvious_fake_patterns_detected"] and not (signals["email_format_valid"] or signals["phone_valid_us"]):
            verified["verification_status"] = "fail"

        # Align contact booleans to deterministic signals.
        verified["contact"]["email_valid"] = bool(signals["email_format_valid"])
        verified["contact"]["phone_valid"] = bool(signals["phone_valid_us"])

        # Keep followups short (1-3).
        verified["required_followups"] = (verified.get("required_followups") or [])[:3]

        session["verification"] = verified
        return verified, phone_e164
    except Exception:
        session["verification"] = fallback
        return fallback, phone_e164


def _build_verification_gate_message(verification):
    status = verification.get("verification_status")
    followups = verification.get("required_followups") or []
    if not isinstance(followups, list):
        followups = []
    followups = [q for q in followups if isinstance(q, str) and q.strip()][:3]

    if status == "fail":
        # Polite correction request (1-3 questions max).
        return "I couldn’t verify the details. Please reply with:\n- Your full name\n- A valid email or U.S. phone number"

    if followups:
        return "\n".join(followups)

    return "Please confirm your name and provide a valid email or U.S. phone number."


def qualify_lead_llm(session):
    """
    Phase 2: qualification should run ONLY after verification_status == "pass".
    """
    verification = session.get("verification") or {}
    fallback = {
        "qualification_status": "follow_up_later",
        "intent_score": 50,
        "intent_bucket": "warm",
        "signals": [],
        "deal_blockers": [],
        "recommended_next_action": "follow_up",
        "follow_up_window_days": 14,
        "one_best_followup_question": "Would you like to schedule a quick call this week, or should I follow up in about two weeks?",
    }

    if verification.get("verification_status") != "pass":
        session["qualification"] = None
        return None

    lead = session.get("lead", {}) or {}
    model_input = {
        "verification_summary": {
            "verification_status": verification.get("verification_status", ""),
            "risk_flags": verification.get("risk_flags", []),
            "verified_fields": verification.get("verified_fields", []),
        },
        "lead_form": {
            "name": lead.get("name", ""),
            "email": lead.get("email", ""),
            "phone": lead.get("phone", ""),
            "company": lead.get("company", ""),
            "role": lead.get("role", ""),
            "preferred_contact_method": lead.get("preferred_contact_method", "unknown"),
            "intent_category": lead.get("intent_category", ""),
            "lead_volume": lead.get("lead_volume", ""),
            "timeline": lead.get("timeline", ""),
        },
        "chat_transcript": (session.get("messages", []) or [])[-8:],
    }

    try:
        resp = openai.ChatCompletion.create(
            model=os.getenv("QUALIFICATION_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": QUALIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(model_input, ensure_ascii=True)},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        content = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(content)
        validated = _validate_qualification_schema(parsed)
        if validated is None:
            session["qualification"] = fallback
            return fallback
        # Observability: mark fallback intent_score if malformed.
        if not isinstance(validated.get("intent_score"), int):
            validated["intent_score"] = 50
            validated["signals"] = (validated.get("signals") or []) + ["intent_score_fallback"]
        session["qualification"] = validated
        return validated
    except Exception:
        session["qualification"] = fallback
        return fallback


def _extract_follow_up_updates(user_input):
    text = (user_input or "").strip().lower()
    updates = {}

    if any(tok in text for tok in ["yes", "yeah", "yep", "sure", "ok", "okay"]):
        updates["permission"] = True
    if any(tok in text for tok in ["no", "nope", "not now", "don't", "do not"]):
        updates["permission"] = False

    if "email" in text and "phone" in text:
        updates["preferred_contact_method"] = "either"
    elif "email" in text:
        updates["preferred_contact_method"] = "email"
    elif any(tok in text for tok in ["phone", "call", "text", "sms"]):
        updates["preferred_contact_method"] = "phone"

    # Time window
    if re.search(r"\b7\b", text) or "week" in text:
        updates["follow_up_window_days"] = 7
    elif re.search(r"\b14\b", text) or "two week" in text or "2 week" in text:
        updates["follow_up_window_days"] = 14
    elif re.search(r"\b30\b", text) or "month" in text:
        updates["follow_up_window_days"] = 30

    return updates


def _build_routed_response(session, qualification):
    # Backward-compatible: treat recommended_next_action as advisory only.
    return "What would you like to do next — book a call or follow up later?"


def decide_next_action(verification, qualification):
    """
    Production-style decision boundary:
    - Verification gates everything.
    - Qualification model output is advisory signals; code decides next_action.
    """
    verification = verification or {}
    qualification = qualification or {}

    if verification.get("verification_status") != "pass":
        return {"next_action": "needs_correction", "follow_up_window_days": 0, "booking_link": BOOKING_LINK, "route_reason": "verification_not_passed"}

    blockers = qualification.get("deal_blockers") or []
    blockers_text = " | ".join([str(b).lower() for b in blockers])
    critical_phrases = [
        "student",
        "just browsing",
        "no budget",
        "no money",
        "wrong service",
        "spam",
        "scam",
        "competitor",
        "not interested",
    ]
    critical_blocker = any(p in blockers_text for p in critical_phrases)

    intent_score = qualification.get("intent_score")
    if not isinstance(intent_score, int):
        intent_score = 50

    if critical_blocker or intent_score < 40:
        reason = "critical_blocker" if critical_blocker else "intent_score<40"
        return {"next_action": "disqualify", "follow_up_window_days": 0, "booking_link": BOOKING_LINK, "route_reason": reason}

    if intent_score >= 75:
        return {"next_action": "book_call", "follow_up_window_days": 0, "booking_link": BOOKING_LINK, "route_reason": "intent_score>=75"}

    # Default follow-up
    days = qualification.get("follow_up_window_days")
    if days not in {7, 14, 30}:
        days = 14
    return {"next_action": "follow_up", "follow_up_window_days": days, "booking_link": BOOKING_LINK, "route_reason": "40<=intent_score<75"}


def build_user_response(session, decision, qualification):
    """
    User-facing routing output (no JSON shown).
    """
    decision = decision or {}
    action = decision.get("next_action")

    if action == "book_call":
        if BOOKING_LINK:
            return f"Thanks — you’re all set. Here’s the link to book a 15‑minute call: {BOOKING_LINK}"
        session["requested_times"] = session.get("requested_times") or ""
        return "I can’t open a booking link right now. What times work for a quick 15‑minute call this week (and what’s your time zone)?"

    if action == "follow_up":
        days = decision.get("follow_up_window_days")
        if days not in {7, 14, 30}:
            days = 14
        return (
            "No problem. Is it okay if I follow up later?\n"
            "If yes, should I reach you by email or phone?\n"
            f"And which timeframe works best: 7, 14, or 30 days? (Default: {days})"
        )

    if action == "disqualify":
        return "Thanks — it doesn’t sound like a fit right now. If anything changes, feel free to reach back out."

    return "What would you like to do next — book a call or follow up later?"

# ----------------------------
# Existing agent behavior (unchanged when verified)
# ----------------------------

# Set up Chroma and embed the FAQ file
chroma_client = chromadb.Client()
chroma_collection = chroma_client.create_collection(name="faq")

# Conversation memory
conversation_history = {}


def load_faq():
    with open("faq.txt", "r") as f:
        docs = f.read().split("\n\n")
    for i, doc in enumerate(docs):
        chroma_collection.add(
            documents=[doc],
            metadatas=[{"source": f"faq_{i}"}],
            ids=[f"id_{i}"],
        )


# Load once on startup
load_faq()


def search_docs(query):
    results = chroma_collection.query(query_texts=[query], n_results=1)
    if results["documents"]:
        # Extract just the answer part (after the question)
        full_doc = results["documents"][0][0]
        if "?" in full_doc:
            # Split on the first question mark and return the answer part
            parts = full_doc.split("?", 1)
            if len(parts) > 1:
                return parts[1].strip()
        return full_doc
    return "Sorry, I couldn't find an answer for that."


def respond_to_objection(text):
    lower = text.lower()
    if "too expensive" in lower:
        return "I understand the concern! We also offer a free plan and competitive pricing for startups."
    elif "not sure" in lower or "don't know" in lower:
        return "No worries — I can help explain more or share a quick demo link."
    return None


def qualify_lead(user_input, session_id):
    """Analyze if this is a qualified lead (existing logic)"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a lead qualification expert. Analyze if the user shows buying intent. Return only 'qualified' or 'not_qualified'.",
                },
                {"role": "user", "content": f"User message: {user_input}"},
            ],
            max_tokens=10,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip().lower()
    except Exception:
        return "not_qualified"


def generate_follow_up(user_input, session_id):
    """Generate contextual follow-up questions (existing logic)"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a sales assistant. Generate 1-2 relevant follow-up questions to continue the conversation naturally. Keep them short and specific.",
                },
                {
                    "role": "user",
                    "content": f"User said: {user_input}\n\nGenerate follow-up questions:",
                },
            ],
            max_tokens=100,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return ""


def run_agent(user_input, session_id="default"):
    # Initialize session if new
    if session_id not in conversation_history:
        conversation_history[session_id] = {
            "messages": [],
            "lead_score": 0,
            "last_contact": datetime.now().isoformat(),
            "guide_offered": False,
            "call_offered": False,
            # Phase 1 additions
            "lead": {"name": "", "email": "", "phone": "", "company": "", "role": "", "preferred_contact_method": "unknown"},
            "signals": {},
            "verification": None,
            # Phase 2 additions
            "qualification": None,
            "follow_up": {
                "permission": "unknown",
                "preferred_contact_method": "unknown",
                "follow_up_window_days": 14,
            },
            "requested_times": "",
        }

    # Add user message to history
    conversation_history[session_id]["messages"].append({"role": "user", "content": user_input})

    # Phase 1: verification gate runs FIRST
    verification, phone_e164 = verify_lead_llm(conversation_history[session_id])
    # Normalize phone in session if possible.
    if phone_e164:
        conversation_history[session_id]["lead"]["phone"] = phone_e164

    if verification.get("verification_status") != "pass":
        conversation_history[session_id]["decision"] = {"next_action": "needs_correction", "follow_up_window_days": 0, "booking_link": BOOKING_LINK}
        gate_message = _build_verification_gate_message(verification)
        conversation_history[session_id]["messages"].append({"role": "assistant", "content": gate_message})
        return gate_message

    # Phase 2: if we're in a follow-up flow, capture user preferences before re-qualifying.
    follow = conversation_history[session_id].get("follow_up") or {}
    if follow and (follow.get("permission") == "unknown" or follow.get("preferred_contact_method") == "unknown"):
        updates = _extract_follow_up_updates(user_input)
        if updates:
            follow.update(updates)
            conversation_history[session_id]["follow_up"] = follow

        if follow.get("permission") is False:
            response_text = "Got it — I won’t follow up. If you want to reconnect later, just message me."
            conversation_history[session_id]["messages"].append({"role": "assistant", "content": response_text})
            return response_text

        if follow.get("permission") is True:
            if follow.get("preferred_contact_method") == "unknown":
                response_text = "Thanks — should I follow up by email or phone?"
                conversation_history[session_id]["messages"].append({"role": "assistant", "content": response_text})
                return response_text
            if follow.get("follow_up_window_days") not in {7, 14, 30}:
                response_text = "When should I follow up: 7, 14, or 30 days?"
                conversation_history[session_id]["messages"].append({"role": "assistant", "content": response_text})
                return response_text

            response_text = f"Perfect — I’ll follow up in {follow.get('follow_up_window_days')} days via {follow.get('preferred_contact_method')}."
            conversation_history[session_id]["messages"].append({"role": "assistant", "content": response_text})
            return response_text

    # Phase 2: run qualification (advisory JSON). Code routes based on recommended_next_action.
    qualification = qualify_lead_llm(conversation_history[session_id])
    conversation_history[session_id]["qualification"] = qualification or None

    decision = decide_next_action(verification, qualification or {})
    conversation_history[session_id]["decision"] = decision

    if decision.get("next_action") == "follow_up":
        # Start/refresh follow-up flow with code-enforced window.
        conversation_history[session_id]["follow_up"] = {
            "permission": "unknown",
            "preferred_contact_method": "unknown",
            "follow_up_window_days": decision.get("follow_up_window_days", 14) or 14,
        }
        response_text = build_user_response(conversation_history[session_id], decision, qualification)
        conversation_history[session_id]["messages"].append({"role": "assistant", "content": response_text})
        return response_text

    if decision.get("next_action") == "disqualify":
        response_text = build_user_response(conversation_history[session_id], decision, qualification)
        conversation_history[session_id]["messages"].append({"role": "assistant", "content": response_text})
        return response_text

    # Verified + not routed to follow-up/disqualify: keep existing behavior, but append booking CTA.
    objection_response = respond_to_objection(user_input)
    if objection_response:
        # If qualified, still include booking CTA.
        if decision.get("next_action") == "book_call":
            cta = build_user_response(conversation_history[session_id], decision, qualification)
            full = f"{objection_response}\n\n{cta}"
            conversation_history[session_id]["messages"].append({"role": "assistant", "content": full})
            return full
        conversation_history[session_id]["messages"].append({"role": "assistant", "content": objection_response})
        return objection_response

    # Get relevant FAQ context
    faq_context = search_docs(user_input)

    # Qualify the lead (existing logic)
    is_qualified = qualify_lead(user_input, session_id)
    if is_qualified == "qualified":
        conversation_history[session_id]["lead_score"] += 1

    # Generate response with context
    try:
        recent_messages = conversation_history[session_id]["messages"][-3:]  # Last 3 messages
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are a dynamic sales assistant.
                - Be conversational and engaging
                - Use the FAQ information provided
                - If lead_score is high, be more direct about next steps (booking a call)
                - Keep responses under 100 words
                - Be enthusiastic but professional""",
                },
                {
                    "role": "user",
                    "content": f"""Context: {context}
                FAQ Info: {faq_context}
                Lead Score: {conversation_history[session_id]['lead_score']}
                User: {user_input}""",
                },
            ],
            max_tokens=150,
            temperature=0.8,
        )

        main_response = response.choices[0].message.content.strip()

        if decision.get("next_action") == "book_call":
            main_response = f"{main_response}\n\n{build_user_response(conversation_history[session_id], decision, qualification)}"

        conversation_history[session_id]["messages"].append({"role": "assistant", "content": main_response})
        return main_response

    except Exception:
        fallback_response = (
            faq_context
            if faq_context != "Sorry, I couldn't find an answer for that."
            else "I'd be happy to help! Could you tell me more about what you're looking for?"
        )
        conversation_history[session_id]["messages"].append({"role": "assistant", "content": fallback_response})
        return fallback_response
