import os
import streamlit as st

from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

# --- Streamlit UI ---
st.set_page_config(page_title="Business Plan Generator", page_icon="💼")

st.title("💼 One-Page Business Plan Generator")
st.write("Generate a concise business plan using AI!")

# Sidebar for API key
st.sidebar.header("API Settings")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

# User inputs
business_name = st.text_input("Business Name")
industry = st.text_input("Industry")
key_points = st.text_area("Key Points / Ideas (comma separated)")
temperature = st.slider("Creativity (Temperature)", 0.0, 1.0, 0.7)

# Generate button
if st.button("Generate Business Plan"):
    if not api_key:
        st.warning("Please enter your OpenAI API key in the sidebar!")
    elif not business_name or not industry or not key_points:
        st.warning("Please fill in all fields!")
    else:
        # Set env var (optional but common)
        os.environ["OPENAI_API_KEY"] = api_key

        # --- Prompt template ---
        prompt = PromptTemplate(
            template=(
                "You are a professional business consultant. "
                "Create a concise one-page business plan for the company '{business_name}' "
                "in the '{industry}' industry. "
                "Include the following key points: {key_points}. "
                "Make it clear, structured, and professional."
            ),
            input_variables=["business_name", "industry", "key_points"],
        )

        # --- LLM ---
        llm = OpenAI(
            temperature=temperature,
            api_key=api_key,
        )

        # Format prompt and call model directly
        formatted_prompt = prompt.format(
            business_name=business_name,
            industry=industry,
            key_points=key_points,
        )
        plan = llm.invoke(formatted_prompt)

        # Display result
        st.subheader("📄 Your One-Page Business Plan")
        st.write(plan)


