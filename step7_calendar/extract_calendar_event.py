import os
import json
from groq import Groq
from datetime import datetime, timedelta, timezone
import uuid
import sys
import subprocess

# ================= CONFIG =================
GROQ_API_KEY = "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"
MODEL = "llama-3.1-8b-instant"

TRANSCRIPTS_DIR = r"D:\meetsnap\transcripts"
OUTPUT_ICS = r"D:\meetsnap\step7_calendar\meeting_event.ics"

DEFAULT_DURATION_MIN = 60
# =========================================


def get_latest_transcript():
    files = [
        os.path.join(TRANSCRIPTS_DIR, f)
        for f in os.listdir(TRANSCRIPTS_DIR)
        if f.endswith(".txt")
    ]
    if not files:
        raise FileNotFoundError("No transcript found")
    return max(files, key=os.path.getmtime)


def read_transcript(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_event_with_ai(transcript):
    client = Groq(api_key=GROQ_API_KEY)

    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
You are a strict JSON generator.

TODAY'S DATE: {today}

TASK:
From the meeting transcript, detect if a meeting or appointment is being scheduled.

OUTPUT RULES (VERY IMPORTANT):
- Return ONLY valid JSON
- Do NOT include explanations
- Do NOT include markdown
- Do NOT include any text outside JSON
- Do NOT include comments or notes

If a meeting exists, return EXACTLY this format:

{{
  "title": "Meeting title",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "duration": 60,
  "location": "Location or Not mentioned"
}}

If NO meeting exists, return exactly:
NO_EVENT

Transcript:
{transcript}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You extract calendar events."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=400
    )

    return response.choices[0].message.content.strip()


# ✅ Escape special characters for Outlook
def escape_text(text):
    if not text:
        return ""
    return text.replace(",", "\\,").replace("\n", "\\n")


def generate_ics(event):
    event_time = event.get("time")

    # ✅ Fix empty or missing time
    if not event_time or event_time.strip() == "" or event_time == "Not mentioned":
        event_time = "09:00"

    duration = event.get("duration", DEFAULT_DURATION_MIN)

    # ✅ Parse local time
    start_dt_local = datetime.strptime(
        f"{event['date']} {event_time}",
        "%Y-%m-%d %H:%M"
    )

    # ✅ Convert to UTC (important for Outlook)
    start_dt_utc = start_dt_local.astimezone(timezone.utc)
    end_dt_utc = start_dt_utc + timedelta(minutes=duration)

    uid = f"{uuid.uuid4()}@meetsnap.ai"
    now_utc = datetime.now(timezone.utc)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MeetSnap//Smart Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",

        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_utc.strftime('%Y%m%dT%H%M%SZ')}",

        # ✅ Proper UTC format with Z
        f"DTSTART:{start_dt_utc.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{end_dt_utc.strftime('%Y%m%dT%H%M%SZ')}",

        f"SUMMARY:{escape_text(event.get('title', 'Meeting'))}",
        "DESCRIPTION:Meeting scheduled via MeetSnap",
        f"LOCATION:{escape_text(event.get('location', 'Not mentioned'))}",

        "STATUS:CONFIRMED",
        "SEQUENCE:0",
        "TRANSP:OPAQUE",
        "CLASS:PUBLIC",
        "PRIORITY:5",

        # ✅ Reminder
        "BEGIN:VALARM",
        "TRIGGER:-PT15M",
        "ACTION:DISPLAY",
        "DESCRIPTION:Reminder",
        "END:VALARM",

        # ✅ Outlook-friendly
        "ORGANIZER;CN=MeetSnap:mailto:meetsnap@ai.app",
        "ATTENDEE;CN=You;RSVP=TRUE:mailto:you@example.com",

        "END:VEVENT",
        "END:VCALENDAR"
    ]

    # ✅ CRLF required by Outlook
    return "\r\n".join(lines) + "\r\n"


def open_calendar_file(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # Windows (Outlook)
        elif sys.platform.startswith("darwin"):
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as e:
        print("⚠️ Could not auto-open calendar:", e)


def main():
    transcript_path = get_latest_transcript()
    print(f"📄 Using transcript: {transcript_path}")

    transcript = read_transcript(transcript_path)

    ai_result = extract_event_with_ai(transcript)

    if ai_result == "NO_EVENT":
        print("⚠️ No calendar event detected")
        return

    try:
        event = json.loads(ai_result)
    except json.JSONDecodeError:
        print("❌ AI output not valid JSON")
        print(ai_result)
        return

    os.makedirs(os.path.dirname(OUTPUT_ICS), exist_ok=True)

    ics_content = generate_ics(event)

    with open(OUTPUT_ICS, "w", encoding="utf-8") as f:
        f.write(ics_content)

    print(f"📅 Calendar event created: {OUTPUT_ICS}")

    open_calendar_file(OUTPUT_ICS)


if __name__ == "__main__":
    main()