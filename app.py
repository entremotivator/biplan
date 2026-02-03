import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import os
from pathlib import Path
import PyPDF2
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import markdown
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Business Plan Generator",
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
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    </style>
""", unsafe_allow_html=True)

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded document (PDF, DOCX, or TXT)"""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension == 'pdf':
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    elif file_extension == 'docx':
        doc = Document(uploaded_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    elif file_extension == 'txt':
        return uploaded_file.read().decode('utf-8')
    
    else:
        st.error("Unsupported file format. Please upload PDF, DOCX, or TXT files.")
        return None

def generate_business_plan(business_description, api_key, model_name):
    """Generate comprehensive business plan using LangChain and OpenAI"""
    
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Initialize the LLM with the latest model
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.7,
        max_tokens=4000
    )
    
    # Create a comprehensive prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are an expert business consultant and strategist with decades of experience in creating comprehensive business plans. 
        Your task is to generate a detailed, professional business plan in Markdown format that includes all standard sections.
        The business plan should be thorough, actionable, and investor-ready."""),
        HumanMessage(content="""Based on the following business description, create a comprehensive business plan in Markdown format.

Business Description:
{business_description}

Generate a complete business plan with the following sections (use Markdown headers and formatting):

# Executive Summary
Provide a compelling overview of the business, its mission, and key highlights.

# Company Overview
## Mission Statement
## Vision Statement
## Company Values
## Legal Structure
## Location and Facilities

# Products and Services
Describe in detail what the business offers, including features, benefits, and unique selling propositions.

# Market Analysis
## Industry Overview
## Target Market
## Market Size and Growth Potential
## Customer Segments
## Market Trends

# Competitive Analysis
## Direct Competitors
## Indirect Competitors
## Competitive Advantages
## SWOT Analysis
### Strengths
### Weaknesses
### Opportunities
### Threats

# Marketing and Sales Strategy
## Marketing Channels
## Pricing Strategy
## Sales Process
## Customer Acquisition Strategy
## Brand Positioning

# Operations Plan
## Production/Service Delivery
## Technology and Equipment
## Suppliers and Partners
## Quality Control

# Management and Organization
## Organizational Structure
## Key Personnel
## Advisory Board
## Hiring Plan

# Financial Projections
## Revenue Model
## Startup Costs
## 3-Year Financial Forecast
### Year 1 Projections
### Year 2 Projections
### Year 3 Projections
## Break-even Analysis
## Funding Requirements

# Milestones and Metrics
## Key Milestones
## Success Metrics
## Timeline

# Risk Analysis and Mitigation
## Potential Risks
## Mitigation Strategies

# Appendix
## Supporting Documents
## Additional Data

Make the plan specific, detailed, and professional. Use realistic estimates and industry-standard practices.""")
    ])
    
    # Generate the business plan
    with st.spinner("🤖 AI is generating your comprehensive business plan... This may take a moment."):
        chain = prompt_template | llm
        response = chain.invoke({"business_description": business_description})
        business_plan_md = response.content
    
    return business_plan_md

def markdown_to_pdf(markdown_text, output_path):
    """Convert Markdown business plan to PDF using ReportLab"""
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2e5090'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#4a628a'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=14
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=20,
        spaceAfter=6,
        leading=14
    )
    
    # Add title page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("BUSINESS PLAN", title_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(PageBreak())
    
    # Process markdown content
    lines = markdown_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 12))
            continue
        
        # Handle headers
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, heading1_style))
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, heading2_style))
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, heading3_style))
        elif line.startswith('#### '):
            text = line[5:].strip()
            story.append(Paragraph(text, heading3_style))
        
        # Handle bullet points
        elif line.startswith('- ') or line.startswith('* '):
            text = '• ' + line[2:].strip()
            story.append(Paragraph(text, bullet_style))
        
        # Handle numbered lists
        elif len(line) > 2 and line[0].isdigit() and line[1:3] in ['. ', ') ']:
            story.append(Paragraph(line, bullet_style))
        
        # Handle bold text
        elif '**' in line:
            text = line.replace('**', '<b>').replace('**', '</b>')
            story.append(Paragraph(text, body_style))
        
        # Regular paragraph
        else:
            story.append(Paragraph(line, body_style))
    
    # Build PDF
    doc.build(story)

def main():
    # Sidebar for API configuration
    with st.sidebar:
        st.title("⚙️ Configuration")
        st.markdown("---")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys"
        )
        
        # Model selection
        model_options = {
            "GPT-4 Turbo": "gpt-4-turbo-preview",
            "GPT-4": "gpt-4",
            "GPT-4o": "gpt-4o",
            "GPT-4o Mini": "gpt-4o-mini",
            "GPT-3.5 Turbo": "gpt-3.5-turbo"
        }
        
        selected_model = st.selectbox(
            "Select Model",
            options=list(model_options.keys()),
            index=2,  # Default to GPT-4o
            help="Choose the OpenAI model to use for generation"
        )
        
        model_name = model_options[selected_model]
        
        st.markdown("---")
        st.markdown("### About")
        st.info(
            "This app uses LangChain and OpenAI's latest models to generate "
            "comprehensive business plans from your business description."
        )
        
        st.markdown("### Supported File Types")
        st.markdown("- PDF (.pdf)")
        st.markdown("- Word (.docx)")
        st.markdown("- Text (.txt)")
    
    # Main content
    st.title("📊 Business Plan Generator")
    st.markdown(
        "Upload your business description document and let AI generate a comprehensive, "
        "professional business plan for you."
    )
    st.markdown("---")
    
    # File upload section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Business Description",
            type=['pdf', 'docx', 'txt'],
            help="Upload a document containing your business description"
        )
    
    with col2:
        st.markdown("### Quick Tips")
        st.markdown("""
        - Include your business idea
        - Mention target audience
        - Describe products/services
        - Note any unique features
        """)
    
    # Text area for manual input
    st.markdown("### Or paste your business description here:")
    manual_input = st.text_area(
        "Business Description",
        height=200,
        placeholder="Enter your business description here...\n\nExample: We are developing an AI-powered mobile app that helps users track their fitness goals through personalized workout plans and nutrition guidance. Our target market is health-conscious millennials aged 25-40 who want convenient, affordable fitness coaching..."
    )
    
    # Generate button
    if st.button("🚀 Generate Business Plan", type="primary"):
        if not api_key:
            st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
            return
        
        # Get business description from file or manual input
        business_description = None
        
        if uploaded_file:
            business_description = extract_text_from_file(uploaded_file)
            if business_description:
                st.success(f"✅ Successfully extracted text from {uploaded_file.name}")
        elif manual_input:
            business_description = manual_input
        else:
            st.error("⚠️ Please upload a file or enter a business description.")
            return
        
        if business_description:
            try:
                # Generate business plan
                business_plan_md = generate_business_plan(
                    business_description,
                    api_key,
                    model_name
                )
                
                # Save markdown file
                md_path = "/home/claude/business_plan.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(business_plan_md)
                
                # Generate PDF
                pdf_path = "/home/claude/business_plan.pdf"
                markdown_to_pdf(business_plan_md, pdf_path)
                
                # Display success message
                st.markdown('<div class="success-message">✨ Business plan generated successfully!</div>', unsafe_allow_html=True)
                st.markdown("---")
                
                # Display the business plan
                st.markdown("## 📄 Generated Business Plan")
                st.markdown(business_plan_md)
                
                st.markdown("---")
                
                # Download buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        st.download_button(
                            label="📥 Download Markdown",
                            data=f.read(),
                            file_name="business_plan.md",
                            mime="text/markdown"
                        )
                
                with col2:
                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download PDF",
                            data=f.read(),
                            file_name="business_plan.pdf",
                            mime="application/pdf"
                        )
                
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()
