import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.chains.summarize import load_summarize_chain
from transformers import T5Tokenizer, T5ForConditionalGeneration
from transformers import pipeline
import torch
import base64
from docx import Document
import os

# model and tokenizer loading
checkpoint = "LaMini-Flan-T5-248M"
tokenizer = T5Tokenizer.from_pretrained(checkpoint)
base_model = T5ForConditionalGeneration.from_pretrained(
    checkpoint, device_map='auto', torch_dtype=torch.float32)

# file loader and preprocessing


def file_preprocessing(file):
    ext = os.path.splitext(file)[-1].lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file)
        pages = loader.load_and_split()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=200, chunk_overlap=50)
        texts = text_splitter.split_documents(pages)
        final_texts = "".join([text.page_content for text in texts])
        return final_texts

    elif ext == ".docx":
        doc = Document(file)
        full_text = "\n".join(
            [para.text for para in doc.paragraphs if para.text.strip()])
        return full_text

    else:
        return ""


# LLM pipeline


def llm_pipeline(filepath):
    pipe_sum = pipeline(
        'summarization',
        model=base_model,
        tokenizer=tokenizer,
        max_length=500,
        min_length=50)
    input_text = file_preprocessing(filepath)
    result = pipe_sum(input_text)
    result = result[0]['summary_text']
    return result


@st.cache_data
# function to display the PDF of a given file
def displayPDF(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    # Embedding PDF in HTML
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'

    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)


# streamlit code
st.set_page_config(layout="wide")


def main():
    st.title("Document Summarization App")

    uploaded_file = st.file_uploader(
        "Upload your PDF or DOCX file", type=['pdf', 'docx'])

    if uploaded_file is not None:
        if st.button("Summarize"):
            col1, col2 = st.columns(2)
            os.makedirs("data", exist_ok=True)
            filepath = os.path.join("data", uploaded_file.name)

            with open(filepath, "wb") as temp_file:
                temp_file.write(uploaded_file.read())

            with col1:
                st.info("Uploaded File")
                if uploaded_file.name.endswith(".pdf"):
                    displayPDF(filepath)
                else:
                    st.write(
                        "DOCX uploaded. Preview not supported, but it's processed.")

            with col2:
                summary = llm_pipeline(filepath)
                st.info("Summarization Complete")
                st.success(summary)
                

if __name__ == "__main__":
    main()