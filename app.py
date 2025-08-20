import streamlit as st
import requests
from fpdf import FPDF
import re
import unicodedata

# ---------- Constants ----------
API_URL = "https://ai.hackclub.com/chat/completions"
HEADERS = {"Content-Type": "application/json"}

# ---------- AI Query ----------
def query_hackclub_ai(task: str, startdate: str, deadline: str) -> str:
    prompt = (
        f"""You are a productivity assistant. Create a schedule for the task: {task}.
        Include milestones, deadlines, and daily goals.
        Do not include any explanation or thinking text.
        Use the start date: {startdate} and deadline: {deadline}.
        Format EXACTLY like this:

        Day 1: August 20, 2025 - Read 100 pages of Book 1
        Milestone: 100 pages completed

        Day 2: August 21, 2025 - Read 100 pages of Book 1
        Milestone: 200 pages completed
        """
    )

    payload = {
        "messages": [
            {"role": "system", "content": "Return only the schedule in the specified format — no intro or explanations."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Error: {e}"

# ---------- Sanitize for Latin-1 ----------
def sanitize_text(text: str) -> str:
    """Remove/replace characters outside Latin-1 range."""
    return ''.join(
        c if ord(c) < 256 else unicodedata.normalize('NFKD', c).encode('latin-1', 'ignore').decode('latin-1')
        for c in text
    )

# ---------- Parse Schedule ----------
def parse_schedule(text: str):
    """Return list of dicts with keys: date, goal, milestone."""
    days = []
    current = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("day"):
            if current and current.get("date"):
                days.append(current)
            if " - " in line:
                date_part, goal_part = line.split(" - ", 1)
            else:
                date_part, goal_part = line, ""
            current = {
                "date": date_part.strip(),
                "goal": goal_part.strip(),
                "milestone": ""
            }
            continue
        if line.lower().startswith("milestone"):
            if current:
                current["milestone"] = line.split(":", 1)[-1].strip()
    if current and current.get("date"):
        days.append(current)
    return days

# ---------- PDF ----------
class SchedulePDF(FPDF):
    def header(self):
        pass  # No header

    def footer(self):
        pass  # No footer

    def add_table(self, schedule_data):
        # Header row
        self.set_font("Arial", "B", 12)
        self.set_fill_color(200, 230, 200)
        self.cell(50, 10, "Day / Date", border=1, align="C", fill=True)
        self.cell(80, 10, "Goal", border=1, align="C", fill=True)
        self.cell(60, 10, "Milestone", border=1, align="C", fill=True)
        self.ln()

        # Rows
        self.set_font("Arial", "", 11)
        fill = False
        for day in schedule_data:
            self.set_fill_color(245, 245, 245) if fill else self.set_fill_color(255, 255, 255)
            fill = not fill
            self.cell(50, 10, sanitize_text(day["date"]), border=1, fill=True)
            self.cell(80, 10, sanitize_text(day["goal"]), border=1, fill=True)
            self.cell(60, 10, sanitize_text(day["milestone"]), border=1, fill=True)
            self.ln()

# ---------- PDF Generator ----------
def generate_pdf_from_schedule(schedule_text: str) -> bytes:
    parsed = parse_schedule(schedule_text)
    pdf = SchedulePDF()
    pdf.add_page()
    pdf.add_table(parsed)
    return pdf.output(dest="S").encode("latin-1", "ignore")

# ---------- Streamlit UI ----------
st.set_page_config(page_title="SchedulerAI", layout="centered")
st.title("SchedulerAI — Minimal Table PDF Planner")

task = st.text_area("Describe your task:")
startdate = st.date_input("Start Date")
deadline = st.date_input("Deadline")

if st.button("Generate Schedule PDF"):
    with st.spinner("Generating your schedule..."):
        schedule_md = query_hackclub_ai(task, startdate, deadline)
        pdf_bytes = generate_pdf_from_schedule(schedule_md)
        st.download_button("Download as PDF", data=pdf_bytes, file_name=f"schedule{task}.pdf")
