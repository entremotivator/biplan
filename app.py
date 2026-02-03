import streamlit as st
import tempfile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.chains import RetrievalQA

st.set_page_config(page_title="Chat With File", layout="wide")
st.title("📄 Chat with your file")

# --- API key input (frontend-style) ---
api_key = st.text_input(
    "Enter your OpenAI API key",
    type="password"
)

if api_key:
    st.session_state["api_key"] = api_key

# --- File upload ---
uploaded_file = st.file_uploader(
    "Upload a PDF or TXT file",
    type=["pdf", "txt"]
)

if "qa_chain" not in st.session_state:
    st.session_state["qa_chain"] = None

if uploaded_file and "api_key" in st.session_state:
    with st.spinner("Processing file..."):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_file.read())
            file_path = tmp.name

        if uploaded_file.name.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)

        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(docs)

        embeddings = OpenAIEmbeddings(
            openai_api_key=st.session_state["api_key"]
        )

        vectorstore = FAISS.from_documents(chunks, embeddings)

        llm = ChatOpenAI(
            temperature=0,
            openai_api_key=st.session_state["api_key"]
        )

        st.session_state["qa_chain"] = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=vectorstore.as_retriever()
        )

    st.success("File ready! Ask a question 👇")

# --- Chat ---
if st.session_state["qa_chain"]:
    query = st.text_input("Your question")

    if query:
        with st.spinner("Thinking..."):
            response = st.session_state["qa_chain"].run(query)
        st.write("### Answer")
        st.write(response)

elif uploaded_file and not api_key:
    st.warning("Please enter your API key first 🔑")
