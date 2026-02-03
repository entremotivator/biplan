import os
import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

# --- Streamlit UI ---
st.set_page_config(page_title="Business Plan Generator", page_icon="💼")

st.title("💼 One-Page Business Plan Generator")
st.write(
    "Generate a detailed, investor-ready one-page business plan, including "
    "mission, market, offer, monetization, and execution roadmap."
)

# Sidebar for API key and advanced settings
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
    ["Concise", "Standard", "In-depth"],
    index=1,
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
    placeholder="e.g., Pitch to investors, clarify strategy, plan MVP launch",
)

# Map detail level to explicit guidance for the model
detail_instructions = {
    "Concise": "Keep each section to 1–2 short paragraphs with bullet points where helpful.",
    "Standard": "Provide 1–3 paragraphs per section with bullets for clarity.",
    "In-depth": "Elaborate each section in multiple paragraphs and bullet lists with specific, concrete details.",
}
selected_detail_instruction = detail_instructions[detail_level]

# Generate button
if st.button("Generate Business Plan"):
    if not api_key:
        st.warning("Please enter your OpenAI API key in the sidebar!")
    elif not business_name or not industry or not value_prop:
        st.warning("Please at least fill in Business Name, Industry, and Key Value Proposition.")
    else:
        # Optional: set env var
        os.environ["OPENAI_API_KEY"] = api_key

        # --- Prompt template ---
        prompt = PromptTemplate(
            template=(
                "You are a seasoned startup and business consultant with experience "
                "writing investor-ready one-page business plans.\n\n"
                "Write a ONE-PAGE business plan for the company '{business_name}' "
                "operating in the '{industry}' industry.\n\n"
                "Context and inputs:\n"
                "- Target customer: {target_customer}\n"
                "- Core value proposition: {value_prop}\n"
                "- Additional key points / ideas: {key_points}\n"
                "- Primary goal for this plan: {primary_goal}\n"
                "- Desired tone: {tone}\n"
                "- Detail level instructions: {detail_instruction}\n\n"
                "Structure the plan with clear markdown section headings using '##' for each major section.\n"
                "Include at least the following sections:\n"
                "1. Overview & Mission\n"
                "2. Problem & Opportunity\n"
                "3. Solution & Product/Service\n"
                "4. Target Market & Customers\n"
                "5. Business Model & Pricing\n"
                "6. Go-To-Market Strategy\n"
                "7. Competitive Advantage\n"
                "8. Operations & Key Resources\n"
                "9. KPIs & Milestones (next 6–12 months)\n"
                "10. Risks & Mitigation\n\n"
                "Requirements:\n"
                "- Write in a persuasive but realistic tone aligned with the requested tone.\n"
                "- Be concrete and specific, not generic.\n"
                "- Use bullet points where it improves clarity.\n"
                "- Keep it to the equivalent of roughly one page of text.\n"
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

        # --- LLM ---
        llm = OpenAI(
            temperature=temperature,
            api_key=api_key,
            # You can set a specific model here if needed, e.g.:
            # model="gpt-4.1-mini",
        )

        # Format prompt and call model directly
        formatted_prompt = prompt.format(
            business_name=business_name,
            industry=industry,
            target_customer=target_customer or "Not specified",
            value_prop=value_prop,
            key_points=key_points or "No extra points provided",
            primary_goal=primary_goal or "Not clearly specified",
            tone=tone,
            detail_instruction=selected_detail_instruction,
        )

        with st.spinner("Generating your one-page business plan..."):
            plan = llm.invoke(formatted_prompt)

        # Display result
        st.subheader("📄 Your One-Page Business Plan")
        st.markdown(plan)
        st.caption(
            "Tip: You can copy this into Notion/Google Docs and iterate on the numbers, "
            "timelines, and KPIs to match your real-world assumptions."
        )

