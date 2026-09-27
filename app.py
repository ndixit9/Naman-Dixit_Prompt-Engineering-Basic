import streamlit as st
from google import genai
import json
import pandas as pd

# Initialize Gemini Client
client = genai.Client(
    vertexai=True,
    project='gd-gcp-gridu-genai',
    location='us-central1'
)

# Set page config
st.set_page_config(page_title="Data Assistant", layout="wide")

# --- CUSTOM CSS TO MATCH SAMPLE UI ---
st.markdown("""
    <style>
    /* 1. Hide radio button circles and style as tabs */
    div[role="radiogroup"] > label > div:first-of-type {
        display: none;
    }
    div[role="radiogroup"] > label {
        background-color: #f4f4f5;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 5px;
        font-weight: 500;
    }
    
    /* 4. Hide the temperature slider number */
    div[data-testid="stSliderThumbValue"] {
        display: none;
    }
    div[data-testid="stSliderTickBar"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Data Assistant")
page = st.sidebar.radio(
    "Navigation", 
    ["🗄️ Data Generation", "💬 Talk to your data"],
    label_visibility="collapsed"
)

if page == "🗄️ Data Generation":
    
    # --- Top Container: Inputs & Parameters ---
    with st.container(border=True):
        st.write("Prompt")
        user_prompt = st.text_input("Prompt", placeholder="Enter your prompt here...", label_visibility="collapsed")
        
        # 2 & 3. Upload SSL Schema layout alignment
        col_upload, col_text = st.columns([1, 3])
        with col_upload:
            # Hiding the default label so only the uploader box shows
            uploaded_file = st.file_uploader("Upload SSL Schema", type=["sql", "json"], label_visibility="collapsed")
        with col_text:
            # Aligning the supported formats text next to the uploader
            st.markdown("<div style='margin-top: 30px; color: #666; font-size: 14px;'>Supported formats: SQL, JSON</div>", unsafe_allow_html=True)
        
        st.write("Advanced Parameters")
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
        with col2:
            max_tokens = st.number_input("Max Tokens", min_value=1, value=100)
            
        if st.button("Generate", type="primary"):
            if uploaded_file is not None and user_prompt:
                ddl_content = uploaded_file.getvalue().decode("utf-8")
                
                with st.spinner("Generating synthetic data..."):
                    try:
                        prompt = f"""
                        You are a database expert. I will provide a SQL DDL schema and instructions.
                        Your task is to generate synthetic data for these tables respecting all constraints, foreign keys, and data types.
                        
                        Schema:
                        {ddl_content}
                        
                        Instructions:
                        {user_prompt}
                        
                        Return ONLY a valid JSON object where the keys are the table names and the values are lists of dictionaries representing the rows. Do not include markdown formatting.
                        """
                        
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt,
                            config=genai.types.GenerateContentConfig(
                                temperature=temperature,
                            )
                        )
                        
                        raw_response = response.text.strip()
                        if raw_response.startswith('```json'):
                            raw_response = raw_response[7:-3].strip()
                        elif raw_response.startswith('```'):
                            raw_response = raw_response[3:-3].strip()
                            
                        st.session_state['generated_data'] = json.loads(raw_response)
                        st.success("Data generated successfully!")
                        
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
            else:
                st.warning("Please upload a DDL schema and enter a prompt.")

    # --- Bottom Container: Data Preview ---
    with st.container(border=True):
        col_title, col_dropdown = st.columns([4, 1])
        with col_title:
            st.write("**Data Preview**")
            
        if 'generated_data' in st.session_state and st.session_state['generated_data']:
            table_names = list(st.session_state['generated_data'].keys())
            
            with col_dropdown:
                selected_table = st.selectbox("Select Table", table_names, label_visibility="collapsed")
            
            if selected_table:
                # Display the actual generated data
                df = pd.DataFrame(st.session_state['generated_data'][selected_table])
                st.dataframe(df, use_container_width=True, hide_index=True)
                
        else:
            # 5. Show the Dummy Data Table (mimics the Sample UI image)
            with col_dropdown:
                st.selectbox("Select Table", ["users"], disabled=True, label_visibility="collapsed")
            
            dummy_data = pd.DataFrame({
                "ID": ["001", "002", "003"],
                "Name": ["Sample Data 1", "Sample Data 2", "Sample Data 3"],
                "Category": ["Category A", "Category B", "Category A"],
                "Value": ["245.50", "127.80", "389.20"]
            })
            st.dataframe(dummy_data, use_container_width=True, hide_index=True)
            
        # Quick edit bar at the bottom
        col_edit, col_btn = st.columns([5, 1])
        with col_edit:
            edit_prompt = st.text_input("Quick Edit", placeholder="Enter quick edit instructions...", label_visibility="collapsed")
        with col_btn:
            st.button("🪄 Submit", type="primary")

elif page == "💬 Talk to your data":
    st.write("Natural language querying interface will go here in the next phase.")