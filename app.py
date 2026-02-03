import os
import streamlit as st

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableSequence

# --- Streamlit UI ---
st.set_page_config(page_title="Business Plan Generator", page_icon="💼")

st.title("💼 LangChain Business Plan Generator (10+ pages)")
st.write(
    "Generate a detailed, multi‑section business plan (approximately ten pages) "
    "using LangChain’s prompt + model pipeline."
)

# Sidebar for API key and settings
st.sidebar.header("API Settings")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

st.sidebar.header("Advanced Settings")
temperature = st.sidebar.slider("Creativity (temperature)", 0.0, 1.0, 0.7)
tone = st.sidebar.selectbox(
    "Tone",
    ["Professional", "Visionary", "Lean startup", "Corporate"],
    index=0,
)
detail_level = st.sidebar.selectbox(
    "Detail level",
    ["High-level", "Detailed", "Very detailed (10 pages)"],
    index=2,
)

# Main inputs
st.subheader("Business Information")
business_name = st.text_input("Business Name", placeholder="e.g., Skyline Analytics")
industry = st.text_input("Industry", placeholder="e.g., Real Estate Analytics SaaS")

st.subheader("Key Inputs")
target_customer = st.text_input(
    "Target Customer",
    placeholder="e.g., Residential real estate agents, small brokerages",
)
value_prop = st.text_area(
    "Key Value Proposition",
    placeholder="e.g., Help agents identify high-intent leads using predictive analytics.",
)
key_points = st.text_area(
    "Additional Key Points / Ideas (comma separated)",
    placeholder="e.g., subscription model, mobile-first, US market, integrate with CRM",
)
primary_goal = st.text_input(
    "Primary Goal for This Plan",
    placeholder="e.g., Pitch to investors, internal roadmap, bank loan application",
)

# Detail‑level → instruction text
if detail_level == "High-level":
    detail_instruction = (
        "Write a concise plan with 1–2 paragraphs per section and minimal bullets."
    )
elif detail_level == "Detailed":
    detail_instruction = (
        "Write a detailed plan with 2–4 paragraphs per section plus bullet lists. "
        "Aim for the equivalent of 4–6 pages of text."
    )
else:
    detail_instruction = (
        "Write a very detailed, investor‑grade business plan with multiple paragraphs "
        "and bullet lists in every section. Include concrete examples, assumptions, and "
        "numbers where reasonable. Aim for the equivalent of at least ten pages of text."
    )

# Build LangChain components once (outside the button if you like)
plan_prompt = PromptTemplate(
    template=(
        "You are a seasoned startup and business consultant who writes detailed, "
        "investor‑ready multi‑page business plans.\n\n"
        "Write a COMPREHENSIVE BUSINESS PLAN (approximately ten pages of content) "
        "for the company '{business_name}' operating in the '{industry}' industry.\n\n"
        "Context and inputs:\n"
        "- Target customer: {target_customer}\n"
        "- Core value proposition: {value_prop}\n"
        "- Additional key points / ideas: {key_points}\n"
        "- Primary goal for this plan: {primary_goal}\n"
        "- Desired tone: {tone}\n"
        "- Detail level instructions: {detail_instruction}\n\n"
        "Structure the plan using clear markdown headings. At minimum, include:\n"
        "1. Executive Summary\n"
        "2. Company Overview & Mission\n"
        "3. Market Analysis\n"
        "4. Customer Segments & Personas\n"
        "5. Problem Statement & Opportunity\n"
        "6. Solution & Product/Service Description\n"
        "7. Business Model & Revenue Streams\n"
        "8. Go-To-Market & Sales Strategy\n"
        "9. Marketing Strategy & Channels\n"
        "10. Competitive Landscape & Differentiation\n"
        "11. Operations Plan (team, processes, tech stack, partners)\n"
        "12. Product Roadmap & Innovation\n"
        "13. Financial Overview (assumptions, revenue drivers, cost structure, break‑even narrative)\n"
        "14. KPIs, Milestones & Timeline (next 12–24 months)\n"
        "15. Risks, Dependencies & Mitigation\n\n"
        "Requirements:\n"
        "- Use descriptive headings and subheadings suitable for a 10‑page written plan.\n"
        "- Provide multiple paragraphs and bullet lists per major section.\n"
        "- Use concrete examples and realistic assumptions where appropriate.\n"
        "- Keep the tone aligned with the specified tone while remaining clear and structured.\n"
    ),
    input_variables=[
        "business_name",
        "industry",
        "target_customer",
        "value_prop",
        "key_points",
        "primary_goal",
        "tone",
        "detail_instruction",
    ],
)

# Output parser
parser = StrOutputParser()

if st.button("Generate Business Plan (LangChain)"):
    if not api_key:
        st.warning("Please enter your OpenAI API key in the sidebar!")
    elif not business_name or not industry or not value_prop:
        st.warning("Please at least fill in Business Name, Industry, and Key Value Proposition.")
    else:
        os.environ["OPENAI_API_KEY"] = api_key

        # LangChain Chat LLM
        chat_llm = ChatOpenAI(
            temperature=temperature,
            api_key=api_key,
            # model="gpt-4.1-mini",  # or your preferred chat model
        )

        # Runnable pipeline: prompt → model → parser
        chain: RunnableSequence = plan_prompt | chat_llm | parser

        # Inputs as a dict for LC pipeline
        chain_input = {
            "business_name": business_name,
            "industry": industry,
            "target_customer": target_customer or "Not specified",
            "value_prop": value_prop,
            "key_points": key_points or "No extra points provided",
            "primary_goal": primary_goal or "Not clearly specified",
            "tone": tone,
            "detail_instruction": detail_instruction,
        }

        with st.spinner("Generating your extended LangChain business plan..."):
            plan_text = chain.invoke(chain_input)

        st.subheader("📄 LangChain‑Generated Business Plan (~10+ pages)")
        st.markdown(plan_text)
        st.caption(
            "Tip: Save this output to a file or doc, then iterate on assumptions, "
            "financials, and timelines as you refine the business."
        )
