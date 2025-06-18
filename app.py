import streamlit as st
import openai
from fpdf import FPDF
import base64

# Set OpenAI API key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to generate schedule using OpenAI API
def generate_schedule(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500
    )
    return response.choices[0].text.strip()

# Function to create a PDF from the schedule
def create_pdf(schedule_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, schedule_text)
    return pdf.output(dest="S").encode("latin-1")

# Streamlit UI components
st.title("AI-Powered Scheduler")

user_input = st.text_area("Describe your scheduling needs:")

if st.button("Generate Schedule"):
    if user_input:
        schedule = generate_schedule(user_input)
        pdf_data = create_pdf(schedule)
        b64_pdf = base64.b64encode(pdf_data).decode("utf-8")
        href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="schedule.pdf">Download your schedule as PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.error("Please enter your scheduling needs.")
