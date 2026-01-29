from flask import Flask, render_template, request, jsonify, send_file
from agent import (
    run_agent,
    conversation_history,
    verify_lead_llm,
    validate_phone_us,
    qualify_lead_llm,
    BOOKING_LINK,
    decide_next_action,
)
import json
from datetime import datetime
import os
import csv

app = Flask(__name__)

# Store captured emails (in production, use a database)
captured_emails = []

LEADS_CSV_V1 = "leads.csv"
LEADS_CSV_V2 = "leads_v2.csv"

LEADS_V2_FIELDS = [
    "timestamp",
    "name",
    "email",
    "phone",
    "phone_e164",
    "product",
    "pain_point",
    "session_id",
    "verification_status",
    "verification_score",
    "risk_flags",
    "qualification_status",
    "intent_score",
    "intent_bucket",
    "combined_score",
    "next_action",
    "follow_up_window_days",
    "preferred_contact_method",
    "route_reason",
]


def save_lead_to_csv(lead_data):
    """Save lead data to the original CSV format for backward compatibility."""
    csv_file = LEADS_CSV_V1
    file_exists = os.path.isfile(csv_file)

    fieldnames = ["timestamp", "name", "email", "product", "pain_point", "session_id"]

    try:
        with open(csv_file, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(
                {
                    "timestamp": lead_data.get("timestamp", datetime.now().isoformat()),
                    "name": lead_data.get("name", ""),
                    "email": lead_data.get("email", ""),
                    "product": lead_data.get("product", ""),
                    "pain_point": lead_data.get("pain_point", ""),
                    "session_id": lead_data.get("session_id", ""),
                }
            )

        return True
    except Exception as e:
        print(f"Error saving lead to CSV: {e}")
        return False


def _ensure_leads_v2_schema():
    """
    Ensure leads_v2.csv exists and has the latest headers.
    If an older header exists, migrate in-place (rewrite) to include new columns.
    """
    csv_file = LEADS_CSV_V2
    if not os.path.exists(csv_file):
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LEADS_V2_FIELDS)
            writer.writeheader()
        return

    try:
        with open(csv_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_fields = reader.fieldnames or []
            rows = list(reader)
        if existing_fields == LEADS_V2_FIELDS:
            return

        # Migrate: preserve existing values, add new empty columns.
        tmp = f"{csv_file}.tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LEADS_V2_FIELDS)
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r.get(k, "") for k in LEADS_V2_FIELDS})
        os.replace(tmp, csv_file)
    except Exception as e:
        print(f"Warning: could not ensure leads_v2.csv schema: {e}")


def upsert_lead_to_csv_v2(lead_row):
    """
    Update the most recent row for session_id if present, else append.
    Only overwrites existing fields when incoming value is non-empty.
    """
    _ensure_leads_v2_schema()
    csv_file = LEADS_CSV_V2
    sid = (lead_row.get("session_id") or "").strip()
    if not sid:
        return False

    try:
        rows = []
        with open(csv_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        idx = None
        for i in range(len(rows) - 1, -1, -1):
            if (rows[i].get("session_id") or "").strip() == sid:
                idx = i
                break

        if idx is None:
            rows.append({k: "" for k in LEADS_V2_FIELDS})
            idx = len(rows) - 1

        for k in LEADS_V2_FIELDS:
            incoming = lead_row.get(k, "")
            if incoming not in (None, ""):
                rows[idx][k] = incoming

        tmp = f"{csv_file}.tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LEADS_V2_FIELDS)
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r.get(k, "") for k in LEADS_V2_FIELDS})
        os.replace(tmp, csv_file)
        return True
    except Exception as e:
        print(f"Error upserting lead to CSV v2: {e}")
        return False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download-guide")
def download_guide():
    """Serve the PDF guide for download"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor("#2c3e50"),
            alignment=1,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor("#34495e"),
        )

        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["Normal"],
            fontSize=11,
            spaceAfter=8,
            textColor=HexColor("#2c3e50"),
        )

        story.append(Paragraph("10 LEAD GENERATION STRATEGIES THAT ACTUALLY WORK", title_style))
        story.append(Spacer(1, 20))

        intro_text = """
        This comprehensive guide will help you implement proven lead generation strategies 
        that will attract qualified prospects and grow your business. Each strategy includes 
        practical tips and actionable steps you can implement immediately.
        """
        story.append(Paragraph(intro_text, body_style))
        story.append(Spacer(1, 20))

        strategies = [
            {
                "title": "1. CONTENT MARKETING",
                "content": "• Create valuable blog posts, videos, and infographics<br/>• Focus on solving your audience's problems<br/>• Use SEO to attract organic traffic",
            },
            {
                "title": "2. SOCIAL MEDIA ENGAGEMENT",
                "content": "• Build relationships on LinkedIn, Twitter, and Facebook<br/>• Share industry insights and thought leadership<br/>• Engage with potential prospects' content",
            },
            {
                "title": "3. EMAIL MARKETING",
                "content": "• Build targeted email lists<br/>• Create compelling lead magnets<br/>• Use automation for follow-up sequences",
            },
            {
                "title": "4. REFERRAL PROGRAMS",
                "content": "• Incentivize existing customers to refer others<br/>• Create a structured referral process<br/>• Track and reward successful referrals",
            },
            {
                "title": "5. PARTNERSHIPS",
                "content": "• Collaborate with complementary businesses<br/>• Cross-promote each other's services<br/>• Share leads and revenue",
            },
            {
                "title": "6. WEBINARS AND EVENTS",
                "content": "• Host educational webinars<br/>• Attend industry conferences<br/>• Network with potential prospects",
            },
            {
                "title": "7. COLD OUTREACH",
                "content": "• Research and personalize your approach<br/>• Use multiple channels (email, LinkedIn, phone)<br/>• Follow up consistently",
            },
            {
                "title": "8. ACCOUNT-BASED MARKETING",
                "content": "• Target specific high-value accounts<br/>• Create personalized campaigns<br/>• Use multiple touchpoints",
            },
            {
                "title": "9. INFLUENCER MARKETING",
                "content": "• Partner with industry influencers<br/>• Leverage their audience and credibility<br/>• Create mutually beneficial relationships",
            },
            {
                "title": "10. OPTIMIZATION AND TESTING",
                "content": "• A/B test your landing pages<br/>• Optimize your conversion funnel<br/>• Continuously improve based on data",
            },
        ]

        for strategy in strategies:
            story.append(Paragraph(strategy["title"], heading_style))
            story.append(Paragraph(strategy["content"], body_style))
            story.append(Spacer(1, 15))

        story.append(Spacer(1, 20))
        story.append(Paragraph("BONUS: AI-POWERED LEAD GENERATION", heading_style))

        bonus_content = """
        • Use chatbots for 24/7 lead qualification<br/>
        • Automate follow-up sequences<br/>
        • Personalize content based on behavior<br/>
        • Score leads automatically
        """
        story.append(Paragraph(bonus_content, body_style))

        story.append(Spacer(1, 20))
        conclusion_text = """
        <b>Remember:</b> Quality over quantity. Focus on attracting and converting the right prospects for your business.

        For more strategies and implementation tips, visit LeadCraft AI at leadcraftai.com
        """
        story.append(Paragraph(conclusion_text, body_style))

        doc.build(story)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="10_lead_generation_strategies.pdf",
            mimetype="application/pdf",
        )
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return jsonify({"error": "Error creating PDF"}), 500


@app.route("/", methods=["POST"])
def handle_old_form():
    """Handle old form POST requests and redirect to the new chatbot"""
    return jsonify(
        {"response": "Please use the chat interface to ask questions.", "show_email_capture": False}
    ), 200


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        session_id = data.get("session_id", "default")

        response = run_agent(user_message, session_id)

        # Phase 2: lead magnet is no longer the primary CTA; do not trigger email capture automatically.
        suggested_questions = generate_suggested_questions(user_message, response)

        # Persist latest verification/qualification snapshots when we have usable lead info.
        session = conversation_history.get(session_id) or {}
        lead = session.get("lead") or {}
        verification = session.get("verification") or {}
        qualification = session.get("qualification") or {}
        follow = session.get("follow_up") or {}
        if lead.get("name") and (lead.get("email") or lead.get("phone")) and verification:
            decision = session.get("decision") or decide_next_action(verification, qualification or {})
            verification_score = verification.get("verification_score")
            intent_score = qualification.get("intent_score")
            combined_score = ""
            if isinstance(verification_score, int) and isinstance(intent_score, int):
                combined_score = round(0.4 * verification_score + 0.6 * intent_score)
            upsert_lead_to_csv_v2(
                {
                    "timestamp": datetime.now().isoformat(),
                    "name": lead.get("name", ""),
                    "email": lead.get("email", ""),
                    "phone": lead.get("phone", ""),
                    "phone_e164": lead.get("phone", "") if (lead.get("phone", "") or "").startswith("+") else "",
                    "product": lead.get("product", ""),
                    "pain_point": lead.get("pain_point", ""),
                    "session_id": session_id,
                    "verification_status": verification.get("verification_status", ""),
                    "verification_score": verification.get("verification_score", ""),
                    "risk_flags": json.dumps(verification.get("risk_flags", []), ensure_ascii=True),
                    "qualification_status": qualification.get("qualification_status", ""),
                    "intent_score": qualification.get("intent_score", ""),
                    "intent_bucket": qualification.get("intent_bucket", ""),
                    "combined_score": combined_score,
                    "next_action": decision.get("next_action", ""),
                    "follow_up_window_days": decision.get("follow_up_window_days", ""),
                    "preferred_contact_method": follow.get("preferred_contact_method", ""),
                    "route_reason": decision.get("route_reason", ""),
                }
            )

        return jsonify(
            {
                "response": response,
                "show_email_capture": False,
                "suggested_questions": suggested_questions,
                "verification": verification or None,
                "qualification": qualification or None,
                "next_action": (session.get("decision") or {}).get("next_action", ""),
                "follow_up_window_days": (session.get("decision") or {}).get("follow_up_window_days", 0),
                "booking_link": BOOKING_LINK or "",
            }
        )
    except Exception:
        return jsonify(
            {"response": "Sorry, I encountered an error. Please try again.", "show_email_capture": False, "suggested_questions": []}
        ), 500


@app.route("/capture-email", methods=["POST"])
def capture_email():
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        session_id = data.get("session_id", "default")

        if not email or "@" not in email:
            return jsonify({"success": False, "message": "Invalid email address"})

        email_record = {
            "email": email,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "source": "chatbot_lead_magnet",
        }
        captured_emails.append(email_record)

        print(f"Email captured: {email} from session {session_id}")
        return jsonify({"success": True, "message": "Email captured successfully"})
    except Exception:
        return jsonify({"success": False, "message": "Error capturing email"}), 500


@app.route("/submit_email", methods=["POST"])
def submit_email():
    """Handle email submission for lead magnet"""
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        session_id = data.get("session_id", "default")

        if not email or "@" not in email:
            return jsonify({"success": False, "message": "Invalid email address"})

        email_record = {
            "email": email,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "source": "chatbot_lead_magnet",
            "lead_magnet": "10_lead_generation_strategies_pdf",
        }
        captured_emails.append(email_record)

        print(f"Lead magnet email captured: {email} from session {session_id}")
        return jsonify({"success": True, "message": "Email captured successfully"})
    except Exception:
        return jsonify({"success": False, "message": "Error capturing email"}), 500


@app.route("/submit_lead", methods=["POST"])
def submit_lead():
    """Handle lead submission from chatbot qualification flow (Phase 2: persist verification + qualification)."""
    try:
        data = request.get_json()

        lead_data = {
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "product": data.get("product", ""),
            "pain_point": data.get("pain_point", ""),
            "session_id": data.get("session_id", "default"),
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "source": "chatbot_lead_qualification",
        }

        # Store into agent session memory so verification has access to lead fields.
        sid = lead_data["session_id"]
        if sid not in conversation_history:
            conversation_history[sid] = {
                "messages": [],
                "lead_score": 0,
                "last_contact": datetime.now().isoformat(),
                "guide_offered": False,
                "call_offered": False,
                "lead": {"name": "", "email": "", "phone": "", "company": "", "role": "", "preferred_contact_method": "unknown"},
                "signals": {},
                "verification": None,
                "qualification": None,
                "follow_up": {
                    "permission": "unknown",
                    "preferred_contact_method": "unknown",
                    "follow_up_window_days": 14,
                },
                "requested_times": "",
            }

        # Normalize phone to E.164 if valid US number.
        phone_ok, phone_e164 = validate_phone_us(lead_data.get("phone", ""))
        phone_to_store = phone_e164 if phone_ok and phone_e164 else lead_data.get("phone", "")
        phone_e164_store = phone_e164 if phone_ok and phone_e164 else ""

        conversation_history[sid]["lead"]["name"] = lead_data.get("name", "")
        conversation_history[sid]["lead"]["email"] = lead_data.get("email", "")
        conversation_history[sid]["lead"]["phone"] = phone_to_store

        # Minimal transcript for verification context (lead capture Q/A).
        conversation_history[sid]["messages"].extend(
            [
                {"role": "assistant", "content": "What's your name?"},
                {"role": "user", "content": lead_data.get("name", "")},
                {"role": "assistant", "content": "What's your email?"},
                {"role": "user", "content": lead_data.get("email", "")},
                {"role": "assistant", "content": "What's your phone number?"},
                {"role": "user", "content": phone_to_store},
                {"role": "assistant", "content": "What product or service do you offer?"},
                {"role": "user", "content": lead_data.get("product", "")},
                {"role": "assistant", "content": "What's your biggest pain point?"},
                {"role": "user", "content": lead_data.get("pain_point", "")},
            ]
        )

        verification, phone_e1642 = verify_lead_llm(conversation_history[sid])
        if phone_e1642:
            conversation_history[sid]["lead"]["phone"] = phone_e1642
            phone_to_store = phone_e1642
            phone_e164_store = phone_e1642

        qualification = None
        if verification.get("verification_status") == "pass":
            qualification = qualify_lead_llm(conversation_history[sid])
            conversation_history[sid]["qualification"] = qualification
        decision = decide_next_action(verification, qualification or {})
        conversation_history[sid]["decision"] = decision

        # Persist to leads_v2.csv (preferred) and keep writing v1 for compatibility.
        q = qualification or {}
        follow = conversation_history[sid].get("follow_up") or {}
        verification_score = verification.get("verification_score")
        intent_score = q.get("intent_score")
        combined_score = ""
        if isinstance(verification_score, int) and isinstance(intent_score, int):
            combined_score = round(0.4 * verification_score + 0.6 * intent_score)
        csv_v2_saved = upsert_lead_to_csv_v2(
            {
                "timestamp": lead_data.get("timestamp", ""),
                "name": lead_data.get("name", ""),
                "email": lead_data.get("email", ""),
                "phone": phone_to_store,
                "phone_e164": phone_e164_store,
                "product": lead_data.get("product", ""),
                "pain_point": lead_data.get("pain_point", ""),
                "session_id": lead_data.get("session_id", ""),
                "verification_status": verification.get("verification_status", ""),
                "verification_score": verification.get("verification_score", ""),
                "risk_flags": json.dumps(verification.get("risk_flags", []), ensure_ascii=True),
                "qualification_status": q.get("qualification_status", ""),
                "intent_score": q.get("intent_score", ""),
                "intent_bucket": q.get("intent_bucket", ""),
                "combined_score": combined_score,
                "next_action": decision.get("next_action", ""),
                "follow_up_window_days": decision.get("follow_up_window_days", ""),
                "preferred_contact_method": follow.get("preferred_contact_method", "") if follow else "",
                "route_reason": decision.get("route_reason", ""),
            }
        )
        csv_v1_saved = save_lead_to_csv(lead_data)

        return jsonify(
            {
                "success": True,
                "message": "Lead captured successfully",
                "lead_id": f"lead_{sid}",
                "verification": verification,
                "qualification": qualification,
                "next_action": decision.get("next_action", ""),
                "follow_up_window_days": decision.get("follow_up_window_days", ""),
                "booking_link": BOOKING_LINK,
                "download_link": "/download-guide",
                "csv_saved": bool(csv_v2_saved or csv_v1_saved),
            }
        )
    except Exception as e:
        print(f"Error capturing lead: {e}")
        return jsonify({"success": False, "message": "Error capturing lead"}), 500


@app.route("/book-call", methods=["POST"])
def book_call():
    """Handle call booking responses"""
    try:
        data = request.get_json()
        user_response = data.get("response", "").lower()

        if "yes" in user_response or "book" in user_response or "call" in user_response:
            return jsonify(
                {
                    "success": True,
                    "message": "Great! I've sent the booking link. Please check your email for the calendar invite. Looking forward to our call! 📞",
                    "booking_link": "https://calendly.com/your-calendar/15min-strategy-call",
                }
            )
        else:
            return jsonify(
                {
                    "success": True,
                    "message": "No worries! If you change your mind, just let me know. I'm here to help with any questions about lead generation strategies.",
                }
            )
    except Exception as e:
        return jsonify({"success": False, "message": f"Error processing booking request: {str(e)}"}), 500


def check_lead_magnet_trigger(user_message, agent_response):
    user_lower = user_message.lower()

    trigger_words = [
        "lead",
        "leads",
        "generation",
        "prospecting",
        "sales",
        "outreach",
        "automation",
        "strategy",
        "guide",
        "pdf",
        "download",
        "free",
        "how to",
        "tips",
        "best practices",
        "strategies",
    ]

    has_trigger_words = any(word in user_lower for word in trigger_words)
    is_qualified = any(word in user_lower for word in ["pricing", "cost", "plan", "demo", "trial", "start"])

    return has_trigger_words or is_qualified


def generate_suggested_questions(user_message, agent_response):
    user_lower = user_message.lower()
    response_lower = agent_response.lower()

    default_suggestions = ["What does LeadCraft AI do?", "Is there a free plan?", "Show me pricing"]

    if any(word in user_lower for word in ["pricing", "cost", "plan", "price"]):
        return ["What's included in the premium plan?", "Is there a free trial?", "Can I cancel anytime?"]

    if any(word in user_lower for word in ["integration", "connect", "crm", "hubspot"]):
        return ["What other integrations do you support?", "How does the setup process work?", "Can I import my existing contacts?"]

    if any(word in user_lower for word in ["demo", "trial", "test", "start"]):
        return ["How do I get started?", "What's the setup time?", "Do you offer onboarding support?"]

    if any(word in user_lower for word in ["lead", "leads", "generation"]):
        return ["How quickly will I see results?", "What kind of leads do you generate?", "Can I customize the AI responses?"]

    if any(word in user_lower for word in ["ai", "artificial intelligence", "machine learning"]):
        return ["How does the AI work?", "Can I train it on my product?", "What makes your AI different?"]

    if "pdf" in response_lower or "guide" in response_lower:
        return ["What other resources do you have?", "Can I see a demo first?", "How do I get started?"]

    return default_suggestions[:3]


@app.route("/captured-emails")
def get_captured_emails():
    return jsonify(captured_emails)


@app.route("/dashboard")
def dashboard():
    """Admin dashboard for client management (prefer leads_v2.csv)."""
    try:
        leads = []
        csv_file = LEADS_CSV_V2 if os.path.exists(LEADS_CSV_V2) else LEADS_CSV_V1

        if os.path.exists(csv_file):
            with open(csv_file, "r", newline="", encoding="utf-8") as csvfile:
                first_line = (csvfile.readline() or "").strip()
                csvfile.seek(0)
                has_header = "," in first_line and not first_line[:4].isdigit()

                if has_header:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        leads.append(row)
                else:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        if not row:
                            continue
                        leads.append(
                            {
                                "timestamp": row[0] if len(row) > 0 else "",
                                "name": row[1] if len(row) > 1 else "",
                                "email": row[2] if len(row) > 2 else "",
                                "product": row[3] if len(row) > 3 else "",
                                "pain_point": row[4] if len(row) > 4 else "",
                                "session_id": row[5] if len(row) > 5 else "",
                                "phone": "",
                                "verification_status": "",
                                "verification_score": "",
                                "qualification_status": "",
                                "intent_score": "",
                                "intent_bucket": "",
                                "next_action": "",
                                "follow_up_window_days": "",
                                "preferred_contact_method": "",
                            }
                        )

        leads.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        total_leads = len(leads)
        today_prefix = datetime.now().date().isoformat()
        recent_leads = len([lead for lead in leads if lead.get("timestamp", "").startswith(today_prefix)])

        return render_template("dashboard.html", leads=leads, total_leads=total_leads, recent_leads=recent_leads)
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        return render_template("dashboard.html", leads=[], total_leads=0, recent_leads=0)


@app.route("/download-leads-csv")
def download_leads_csv():
    """Download leads CSV file for Excel"""
    try:
        csv_file = LEADS_CSV_V2 if os.path.exists(LEADS_CSV_V2) else LEADS_CSV_V1

        if not os.path.exists(csv_file):
            with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
                if csv_file == LEADS_CSV_V2:
                    writer = csv.DictWriter(csvfile, fieldnames=LEADS_V2_FIELDS)
                else:
                    writer = csv.DictWriter(
                        csvfile, fieldnames=["timestamp", "name", "email", "product", "pain_point", "session_id"]
                    )
                writer.writeheader()

        return send_file(csv_file, as_attachment=True, download_name="leads_export.csv", mimetype="text/csv")
    except Exception as e:
        print(f"Error downloading CSV: {e}")
        return jsonify({"error": "Error downloading CSV file"}), 500


if __name__ == "__main__":
    app.run(debug=True)
