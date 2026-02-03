import streamlit as st
import os

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from pypdf import PdfReader
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import markdown
from bs4 import BeautifulSoup


# -----------------------------
# Helper functions
# -----------------------------
def read_uploaded_file(uploaded_file):
    """Extract text from uploaded files (PDF, TXT, DOCX)"""
    try:
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
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return ""


def generate_pdf_from_markdown(md_text, filename="business_plan.pdf"):
    """Convert Markdown to PDF with better formatting"""
    try:
        # Convert markdown to HTML
        html_text = markdown.markdown(md_text)
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Setup PDF
        styles = getSampleStyleSheet()
        
        # Create custom styles
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='darkblue',
            spaceAfter=12,
            alignment=TA_LEFT
        ))
        
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='navy',
            spaceAfter=10,
            spaceBefore=12
        ))
        
        story = []
        
        # Parse HTML and convert to PDF elements
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol']):
            if element.name == 'h1':
                story.append(Paragraph(element.get_text(), styles['CustomTitle']))
                story.append(Spacer(1, 0.2*inch))
            elif element.name == 'h2':
                story.append(Paragraph(element.get_text(), styles['CustomHeading']))
                story.append(Spacer(1, 0.1*inch))
            elif element.name == 'h3':
                story.append(Paragraph(element.get_text(), styles['Heading3']))
            elif element.name in ['p', 'li']:
                text = element.get_text()
                if text.strip():
                    story.append(Paragraph(text, styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        pdf = SimpleDocTemplate(filename)
        pdf.build(story)
        
        return filename
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None


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
    st.markdown("**Model Options:**")
    model_choice = st.selectbox(
        "Select Model",
        ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0
    )
    
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1)
    
    st.markdown("---")
    st.info("💡 Tip: Lower temperature = more focused output")


# File upload
uploaded_file = st.file_uploader(
    "Upload your business description (PDF, TXT, or DOCX)",
    type=["pdf", "txt", "docx"]
)

generate_btn = st.button("🚀 Generate Business Plan", type="primary")


# -----------------------------
# Main Logic
# -----------------------------
if generate_btn:
    if not openai_api_key:
        st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        st.stop()

    if not uploaded_file:
        st.error("⚠️ Please upload a business description file.")
        st.stop()

    with st.spinner("📖 Reading document..."):
        business_description = read_uploaded_file(uploaded_file)

    if not business_description.strip():
        st.error("⚠️ Uploaded file appears to be empty.")
        st.stop()

    # Display preview of uploaded content
    with st.expander("📄 View Uploaded Business Description"):
        st.text_area("Content", business_description, height=200)

    # Initialize LLM
    try:
        llm = ChatOpenAI(
            model=model_choice,
            temperature=temperature,
            openai_api_key=openai_api_key
        )

        prompt = PromptTemplate(
            input_variables=["description"],
            template="""
You are a senior business strategist and consultant with expertise in creating comprehensive business plans.

Using the business description below, generate a **professional business plan in Markdown format**.

Include the following sections with detailed, actionable content:

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

Write clearly, concisely, and professionally. Use bullet points where appropriate for readability.
Provide specific, actionable insights based on the business description provided.
"""
        )

        chain = LLMChain(llm=llm, prompt=prompt)

        with st.spinner("🤖 Generating business plan with AI..."):
            business_plan_md = chain.run(description=business_description)

        # Display Markdown
        st.success("✅ Business plan generated successfully!")
        st.markdown("---")
        st.subheader("📄 Generated Business Plan")
        st.markdown(business_plan_md)

        # Generate PDF
        with st.spinner("📑 Creating PDF..."):
            pdf_file = generate_pdf_from_markdown(business_plan_md)

        # Download buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
