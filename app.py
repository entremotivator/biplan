import streamlit as st
import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

from pypdf import PdfReader
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
import markdown
from bs4 import BeautifulSoup
import re


# -----------------------------
# Helper functions
# -----------------------------
def read_uploaded_file(uploaded_file):
    """Extract text from uploaded files (PDF, TXT, DOCX)"""
    try:
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text

        elif uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")

        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

        else:
            return ""
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return ""


def clean_text_for_pdf(text):
    """Clean text to be PDF-compatible"""
    # Remove or replace problematic characters
    text = text.replace('\u2019', "'")  # smart quote
    text = text.replace('\u2018', "'")  # smart quote
    text = text.replace('\u201c', '"')  # smart quote
    text = text.replace('\u201d', '"')  # smart quote
    text = text.replace('\u2013', '-')  # en dash
    text = text.replace('\u2014', '--')  # em dash
    text = text.replace('\u2022', '*')  # bullet
    # Remove any other non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text


def generate_pdf_from_markdown(md_text, filename="business_plan.pdf"):
    """Convert Markdown to PDF with better formatting"""
    try:
        # Clean the markdown text
        md_text = clean_text_for_pdf(md_text)
        
        # Convert markdown to HTML
        html_text = markdown.markdown(md_text)
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Setup PDF
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='darkblue',
            spaceAfter=12,
            spaceBefore=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='navy',
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            name='CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        story = []
        
        # Parse HTML and convert to PDF elements
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'li']):
            text = element.get_text().strip()
            if not text:
                continue
                
            if element.name == 'h1':
                story.append(Paragraph(text, title_style))
                story.append(Spacer(1, 0.2*inch))
            elif element.name == 'h2':
                story.append(Paragraph(text, heading_style))
                story.append(Spacer(1, 0.15*inch))
            elif element.name == 'h3':
                story.append(Paragraph(text, styles['Heading3']))
                story.append(Spacer(1, 0.1*inch))
            elif element.name in ['p', 'li']:
                # Add bullet for list items
                if element.name == 'li':
                    text = f"• {text}"
                story.append(Paragraph(text, normal_style))
        
        # Build PDF
        pdf = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        pdf.build(story)
        
        return filename
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None


def generate_business_plan(business_description, llm):
    """Generate business plan using the LLM"""
    prompt_template = """You are a senior business strategist and consultant with expertise in creating comprehensive business plans.

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
Make sure to use only standard ASCII characters in your output.
"""
    
    prompt = PromptTemplate(
        input_variables=["description"],
        template=prompt_template
    )
    
    # Format the prompt with the description
    formatted_prompt = prompt.format(description=business_description)
    
    # Use invoke method for newer LangChain versions
    response = llm.invoke(formatted_prompt)
    
    # Extract content from response
    if hasattr(response, 'content'):
        return response.content
    else:
        return str(response)


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(
    page_title="AI Business Plan Generator",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 AI Business Plan Generator")
st.caption("Upload a business description → Get a full business plan (Markdown + PDF)")

# Sidebar – API Key
with st.sidebar:
    st.header("🔑 OpenAI Settings")
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys"
    )
    
    st.markdown("---")
    st.markdown("**Model Options:**")
    model_choice = st.selectbox(
        "Select Model",
        ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0,
        help="GPT-4o recommended for best results"
    )
    
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        help="Lower = more focused, Higher = more creative"
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** Lower temperature = more focused output")
    
    st.markdown("---")
    st.markdown("### 📚 Requirements")
    st.code("""
streamlit
langchain
langchain-openai
langchain-core
openai
pypdf
python-docx
markdown
reportlab
beautifulsoup4
    """)


# Main area
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload your business description (PDF, TXT, or DOCX)",
        type=["pdf", "txt", "docx"],
        help="Upload a document containing your business idea or description"
    )

with col2:
    st.markdown("##### Supported formats:")
    st.markdown("- 📄 PDF (.pdf)")
    st.markdown("- 📝 Text (.txt)")
    st.markdown("- 📘 Word (.docx)")

generate_btn = st.button("🚀 Generate Business Plan", type="primary", use_container_width=True)


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

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Read file
    status_text.text("📖 Reading document...")
    progress_bar.progress(20)
    business_description = read_uploaded_file(uploaded_file)

    if not business_description.strip():
        st.error("⚠️ Uploaded file appears to be empty.")
        st.stop()

    # Display preview of uploaded content
    with st.expander("📄 View Uploaded Business Description"):
        st.text_area("Content Preview", business_description[:1000] + "..." if len(business_description) > 1000 else business_description, height=200, disabled=True)
        st.caption(f"Total characters: {len(business_description)}")

    progress_bar.progress(40)

    # Initialize LLM
    try:
        status_text.text("🔧 Initializing AI model...")
        llm = ChatOpenAI(
            model=model_choice,
            temperature=temperature,
            openai_api_key=openai_api_key
        )

        status_text.text("🤖 Generating business plan with AI...")
        progress_bar.progress(60)
        
        business_plan_md = generate_business_plan(business_description, llm)

        progress_bar.progress(80)
        status_text.text("✅ Business plan generated!")

        # Display success message
        st.success("✅ Business plan generated successfully!")
        
        # Display Markdown
        st.markdown("---")
        st.subheader("📄 Generated Business Plan")
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["📖 Formatted View", "📝 Raw Markdown"])
        
        with tab1:
            st.markdown(business_plan_md)
        
        with tab2:
            st.code(business_plan_md, language="markdown")

        # Generate PDF
        status_text.text("📑 Creating PDF...")
        progress_bar.progress(90)
        
        pdf_file = generate_pdf_from_markdown(business_plan_md)

        progress_bar.progress(100)
        status_text.text("🎉 All done!")

        # Download buttons
        st.markdown("---")
        st.subheader("⬇️ Download Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Download Markdown (.md)",
                data=business_plan_md,
                file_name="business_plan.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col2:
            if pdf_file and os.path.exists(pdf_file):
                with open(pdf_file, "rb") as f:
                    pdf_data = f.read()
                    st.download_button(
                        label="📥 Download PDF (.pdf)",
                        data=pdf_data,
                        file_name="business_plan.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                # Clean up PDF file
                try:
                    os.remove(pdf_file)
                except:
                    pass
            else:
                st.warning("⚠️ PDF generation failed. Please download the Markdown version.")

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.info("Please check your API key and try again.")
        
        # Show detailed error in expander
        with st.expander("🔍 Error Details"):
            st.code(str(e))

else:
    # Show instructions when no generation is in progress
    st.markdown("---")
    st.markdown("### 📝 How to use:")
    st.markdown("""
    1. Enter your **OpenAI API key** in the sidebar
    2. **Upload** a business description file (PDF, TXT, or DOCX)
    3. Click **Generate Business Plan**
    4. **Download** your professional business plan in Markdown or PDF format
    """)
    
    st.markdown("---")
    st.markdown("### ✨ Features:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Comprehensive**")
        st.caption("10 detailed sections covering all aspects of your business")
    
    with col2:
        st.markdown("**🤖 AI-Powered**")
        st.caption("Powered by GPT-4o for professional-quality output")
    
    with col3:
        st.markdown("**📥 Multiple Formats**")
        st.caption("Download as Markdown or beautifully formatted PDF")
