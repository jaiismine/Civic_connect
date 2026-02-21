"""CivicConnect — AI Features (Classifier, Sentiment, Chatbot)"""
import anthropic, json
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
MODEL  = "claude-opus-4-6"

# ── Feature 1: Classifier ────────────────────────────────────
def classify_report(title, description):
    prompt = (
        "You are a civic issue classifier. Analyze the report and respond ONLY with JSON.\n"
        f"Title: {title}\nDescription: {description}\n\n"
        "Return ONLY this JSON structure, no extra text:\n"
        "{\"category\":\"<Roads|Infrastructure|Sanitation|Utilities|Parks & Recreation|Public Safety|Drainage|Street Lighting|Other>\","
        "\"severity\":\"<Low|Medium|High|Critical>\","
        "\"summary\":\"<one sentence>\","
        "\"keywords\":[\"kw1\",\"kw2\"],"
        "\"urgent\":false,"
        "\"reason\":\"<why this severity>\"}"
    )
    try:
        r = client.messages.create(model=MODEL, max_tokens=400,
                messages=[{"role":"user","content":prompt}])
        t = r.content[0].text.strip()
        if t.startswith("```"):
            t = t.split("```")[1]
            if t.startswith("json"): t = t[4:]
        return json.loads(t.strip())
    except Exception as e:
        return {"category":"Other","severity":"Medium","summary":description[:100],
                "keywords":[],"urgent":False,"reason":"AI unavailable","error":str(e)}

# ── Feature 2: Sentiment ─────────────────────────────────────
def analyze_sentiment(reports):
    if not reports: return []
    items = [{"id":r.get("id"),"title":r.get("title",""),
              "description":(r.get("description") or "")[:150],
              "severity":r.get("severity","Medium"),
              "status":r.get("status","Pending"),
              "days_old":r.get("days_old",0)} for r in reports]
    prompt = (
        "Analyze urgency/sentiment of these citizen civic reports.\n"
        "For each return: {id, sentiment_score(1-10), sentiment_label(Calm/Concerned/Frustrated/Urgent/Critical),"
        "sentiment_color(green/yellow/orange/red/darkred), sentiment_emoji, ai_priority(bool), ai_note(short str)}\n"
        "Return a JSON array only. No extra text.\n"
        f"Reports: {json.dumps(items)}"
    )
    try:
        r = client.messages.create(model=MODEL, max_tokens=2000,
                messages=[{"role":"user","content":prompt}])
        t = r.content[0].text.strip()
        if t.startswith("```"):
            t = t.split("```")[1]
            if t.startswith("json"): t = t[4:]
        smap = {s["id"]:s for s in json.loads(t.strip())}
        enriched = []
        for rep in reports:
            rd = dict(rep)
            s  = smap.get(rd.get("id"), {})
            rd.update({"sentiment_score": s.get("sentiment_score",5),
                       "sentiment_label": s.get("sentiment_label","Concerned"),
                       "sentiment_color": s.get("sentiment_color","yellow"),
                       "sentiment_emoji": s.get("sentiment_emoji","😐"),
                       "ai_priority":     s.get("ai_priority",False),
                       "ai_note":         s.get("ai_note","")})
            enriched.append(rd)
        enriched.sort(key=lambda x: (not x["ai_priority"], -x["sentiment_score"]))
        return enriched
    except Exception as e:
        for rep in reports:
            rd = dict(rep)
            rd.update({"sentiment_score":5,"sentiment_label":"Concerned",
                       "sentiment_color":"yellow","sentiment_emoji":"😐",
                       "ai_priority":False,"ai_note":f"AI unavailable"})
        return [dict(r) for r in reports]

# ── Feature 3: Chatbot ───────────────────────────────────────
def chat_with_ai(user_message, chat_history, user_context):
    rep_lines = "\n".join(
        [f"- {r['report_id']}: {r['title']} ({r['severity']}, {r['status']})"
         for r in user_context.get("reports",[])[:5]]
    ) or "No reports yet."
    system = (
        f"You are CivicAssist, AI support for CivicConnect.\n"
        f"Citizen: {user_context.get('name','Citizen')}\n"
        f"Their reports:\n{rep_lines}\n\n"
        "Be empathetic, concise, professional. Max 3 sentences.\n"
        "Always respond in JSON: {reply, action(none|escalate|redirect_community|redirect_support|show_reports), action_label, quick_replies[3]}"
    )
    msgs = [{"role":h["role"],"content":h["content"]} for h in chat_history[-10:]]
    msgs.append({"role":"user","content":user_message})
    try:
        r = client.messages.create(model=MODEL, max_tokens=500, system=system, messages=msgs)
        t = r.content[0].text.strip()
        if t.startswith("```"):
            t = t.split("```")[1]
            if t.startswith("json"): t = t[4:]
        return json.loads(t.strip())
    except Exception as e:
        return {"reply":"I am having trouble connecting. Please try the support form below.",
                "action":"none","action_label":"",
                "quick_replies":["Show my reports","How to escalate?","Contact city hall"]}
