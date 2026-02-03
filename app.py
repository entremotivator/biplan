import streamlit as st
import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

from pypdf import PdfReader
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import markdown



# -----------------------------
# Helper functions
# -----------------------------
def read_uploaded_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

    elif uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")

    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        return "\n".join([p.text for p in doc.paragraphs])

    else:
        return ""


def generate_pdf_from_markdown(md_text, filename="business_plan.pdf"):
    html_text = markdown.markdown(md_text)
    styles = getSampleStyleSheet()
    story = []

    for line in html_text.split("\n"):
        story.append(Paragraph(line, styles["Normal"]))

    pdf = SimpleDocTemplate(filename)
    pdf.build(story)

    return filename


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="AI Business Plan Generator", layout="wide")

st.title("📊 AI Business Plan Generator")
st.caption("Upload a business description → Get a full business plan (Markdown + PDF)")

# Sidebar – API Key
with st.sidebar:
    st.header("🔑 OpenAI Settings")
    openai_api_key = st.text_input("OpenAI API Key", type="password")

    st.markdown("---")
    st.markdown("**Model:** gpt-4.1 / gpt-4o (latest)")


# File upload
uploaded_file = st.file_uploader(
    "Upload your business description (PDF, TXT, or DOCX)",
    type=["pdf", "txt", "docx"]
)

generate_btn = st.button("🚀 Generate Business Plan")


# -----------------------------
# Main Logic
# -----------------------------
if generate_btn:
    if not openai_api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
        st.stop()

    if not uploaded_file:
        st.error("Please upload a business description file.")
        st.stop()

    with st.spinner("Reading document..."):
        business_description = read_uploaded_file(uploaded_file)

    if not business_description.strip():
        st.error("Uploaded file appears to be empty.")
        st.stop()

    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4.1",
        temperature=0.3,
        openai_api_key=openai_api_key
    )

    prompt = PromptTemplate(
        input_variables=["description"],
        template="""
You are a senior business strategist.

Using the business description below, generate a **professional business plan in Markdown**.

Include the following sections:

# Executive Summary
# Company Overview
# Market Analysis
# Products & Services
# Business Model
# Go-To-Market Strategy
# Competitive Advantage
# Operations Plan
# Financial Projections (3-Year)
# Risks & Mitigation
# Conclusion

Business Description:
{description}

Write clearly, concisely, and professionally.
"""
    )

    chain = LLMChain(llm=llm, prompt=prompt)

    with st.spinner("Generating business plan..."):
        business_plan_md = chain.run(description=business_description)

    # Display Markdown
    st.subheader("📄 Generated Business Plan (Markdown)")
    st.markdown(business_plan_md)

    # Generate PDF
    with st.spinner("Creating PDF..."):
        pdf_file = generate_pdf_from_markdown(business_plan_md)

    # Download buttons
    st.markdown("---")
    st.download_button(
        "⬇️ Download Business Plan (Markdown)",
        business_plan_md,
        file_name="business_plan.md",
        mime="text/markdown"
    )

    with open(pdf_file, "rb") as f:
        st.download_button(
            "⬇️ Download Business Plan (PDF)",
            f,
            file_name="business_plan.pdf",
            mime="application/pdf"
        )

    st.success("Business plan generated successfully.")
