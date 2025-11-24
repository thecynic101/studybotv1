import streamlit as st
import google.generativeai as genai
import PyPDF2
from PIL import Image
import io
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="StudyBot Pro", page_icon="🎓", layout="wide")

# --- AUTHENTICATION (The Safe Way) ---
# We try to get the key from Streamlit Secrets.
# If it's not there, we ask the user for it (fallback).
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    api_key = st.sidebar.text_input("⚠️ Admin Mode: Enter API Key", type="password")

# --- LOGIC FUNCTIONS ---
def extract_text_with_pages(pdf_files):
    full_text = ""
    for pdf_file in pdf_files:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        doc_name = pdf_file.name
        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            full_text += f"\n\n--- Source: {doc_name}, Page {i+1} ---\n{text}"
    return full_text

def get_gemini_response(api_key, study_material, image_input):
    genai.configure(api_key=api_key)
    # Using Flash for speed and long context
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = """
    You are an expert academic tutor.
    
    TASK:
    1. Analyze the exam questions in the image.
    2. Answer them using ONLY the provided Study Material.
    3. For every answer, you MUST cite the (Source, Page Number).
    4. If the answer is not in the material, state "Not found in provided notes."
    
    FORMAT:
    Question 1: [Question Text]
    Answer: [Detailed Answer]
    📍 Citation: [Source, Page X]
    
    Study Material:
    """
    
    # Error handling for limits
    try:
        response = model.generate_content([prompt + study_material, image_input])
        return response.text
    except Exception as e:
        if "429" in str(e):
            return "⚠️ SERVER BUSY: Too many students are studying right now. Please wait 1 minute and try again."
        else:
            return f"Error: {e}"

# --- UI ---
st.title("🎓 StudyBot: Automate Your Revision")
st.markdown("Upload your handouts + Past Questions -> Get a Cited Answer Sheet.")

# Use Session State to remember the result so it doesn't vanish
if 'answer_sheet' not in st.session_state:
    st.session_state['answer_sheet'] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Your Materials")
    uploaded_files = st.file_uploader("Upload Handouts (PDF)", type=['pdf'], accept_multiple_files=True)
    
    st.subheader("2. The Exam")
    question_image = st.file_uploader("Upload Question Paper (Image)", type=['png', 'jpg', 'jpeg'])
    
    generate_btn = st.button("🚀 Generate Cheat Sheet", type="primary", use_container_width=True)

with col2:
    st.subheader("3. The Answers")
    
    if generate_btn:
        if not api_key:
            st.error("API Key missing. Contact Admin.")
        elif not uploaded_files or not question_image:
            st.warning("Please upload both handouts and questions.")
        else:
            with st.spinner("Analyzing text... (This takes about 15-30 seconds)"):
                # 1. Process PDFs
                raw_text = extract_text_with_pages(uploaded_files)
                # 2. Process Image
                img = Image.open(question_image)
                # 3. AI Magic
                result = get_gemini_response(api_key, raw_text, img)
                
                # Save to session state
                st.session_state['answer_sheet'] = result
                st.rerun() # Refresh to show result

    # Display the result if it exists in memory
    if st.session_state['answer_sheet']:
        st.markdown(st.session_state['answer_sheet'])
        
        # DOWNLOAD BUTTON
        st.download_button(
            label="📥 Download Answer Sheet (.txt)",
            data=st.session_state['answer_sheet'],
            file_name="studybot_answers.txt",
            mime="text/plain",
            use_container_width=True
        )
