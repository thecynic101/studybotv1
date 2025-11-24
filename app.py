import streamlit as st
import google.generativeai as genai
import PyPDF2
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="StudyBot: AI Maxxing", layout="wide")

# --- SIDEBAR: SETTINGS ---
st.sidebar.title("⚙️ Settings")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# --- MAIN PAGE ---
st.title("📚 StudyBot: The AI Maxxer")
st.write("Upload your course materials and your past questions. The AI will find the answers strictly from your notes.")

# --- STEP 1: UPLOAD MATERIALS ---
st.header("1. Upload Study Materials (PDFs)")
uploaded_files = st.file_uploader("Drop your handouts/textbooks here", type=['pdf'], accept_multiple_files=True)

# --- STEP 2: UPLOAD QUESTIONS ---
st.header("2. Upload Past Questions")
st.write("Upload an image of the question paper (e.g., taken with your phone).")
question_image = st.file_uploader("Drop the question paper image here", type=['png', 'jpg', 'jpeg'])

# --- LOGIC FUNCTIONS ---

def extract_text_with_pages(pdf_files):
    """Reads the PDF and keeps track of page numbers."""
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
    
    # This prints available models to your Command Prompt (Black Window) for debugging
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

    # We try to use the Flash model. 
    # Note: We are using the generic 'gemini-2.5-flash' which is the current standard.
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = """
    You are a strict, academic teaching assistant for a Nigerian University student.
    
    Your Task:
    1. Analyze the attached image of the exam questions.
    2. Read the provided Study Material text below.
    3. For EACH question found in the image, write a Theory/Essay style answer.
    
    CRITICAL RULES:
    - You must ONLY use the information provided in the "Study Material" text.
    - If the answer is found, you must cite the Source and Page Number at the end of the answer.
    - If the answer is NOT found in the text, write "NOT FOUND IN PROVIDED MATERIALS" in bold. Do not attempt to guess or use outside knowledge.
    - Be concise but detailed enough for a university exam.
    
    Study Material:
    """
    
    response = model.generate_content([prompt + study_material, image_input])
    return response.text

# --- THE "GO" BUTTON ---
if st.button("Generate Answers"):
    if not api_key:
        st.error("Please enter your API Key in the sidebar!")
    elif not uploaded_files:
        st.error("Please upload study materials!")
    elif not question_image:
        st.error("Please upload a question paper!")
    else:
        with st.spinner("Reading textbooks and analyzing questions... (This might take a moment)"):
            try:
                study_text = extract_text_with_pages(uploaded_files)
                image = Image.open(question_image)
                answer_sheet = get_gemini_response(api_key, study_text, image)
                st.success("Done! Here are your answers:")
                st.markdown(answer_sheet)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")