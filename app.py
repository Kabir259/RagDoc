import streamlit as st
from query_data import query_rag
import os
import shutil
from populate_database import main as populate_database, clear_database

# Define k and similarity_threshold as global variables
k = 3
similarity_threshold = 0.5

def display_response(response, sources):
    # Display main response
    st.markdown(response)
    
    # Display sources as hyperlinks
    if sources:
        st.markdown("*Sources:*")
        source_buttons = ""
        for idx, source in enumerate(sources, 1):
            document_path = source['source']
            page_number = source['page']
            file_name = os.path.basename(document_path)
            download_link = f"/{document_path}"
            source_buttons += f"""
            <a href="{download_link}" download="{file_name}" target="_blank" style="text-decoration: none;">
                <div style="border: 1px solid #ccc; padding: 5px 10px; margin: 2px; border-radius: 5px; background-color: #f0f0f0; display: inline-block; font-size: 12px;">
                    <strong>Page {page_number}</strong>
                </div>
            </a>
            """
        st.markdown(source_buttons, unsafe_allow_html=True)

def clear_uploaded_documents():
    # Clear the private data directory
    private_data_path = "data/private"
    if os.path.exists(private_data_path):
        shutil.rmtree(private_data_path)
        os.makedirs(private_data_path)
    
    # Clear the database
    clear_database()
    
    # Repopulate the database with public data
    populate_database()

def main():
    global k, similarity_threshold

    st.title("RagDoc 📄")
    st.markdown(
        """<div>Made by: <a href="https://www.linkedin.com/in/kabir259/" target="_blank">Kabir Kumar</a> | <a href="mailto:ee3210741@iitd.ac.in">ee3210741@iitd.ac.in</a> | IIT Delhi</div>""",
        unsafe_allow_html=True
    )




    # Sidebar for developer mode
    st.sidebar.title("Developer Mode")
    k = st.sidebar.slider("No. of references:", min_value=1, max_value=10, value=3)
    st.sidebar.markdown("The number of references to include in the response.")
    st.sidebar.markdown("---")
    similarity_threshold = st.sidebar.slider("Similarity threshold:", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
    st.sidebar.markdown("For a query with ```Similarity(query,data) <= Threshold```, the fallback response is triggered.")
    st.sidebar.markdown("---")
    enable_history = st.sidebar.checkbox("Enable chat history", value=True)
    st.sidebar.markdown("---")
    
    

    # Collapsible section for uploading PDFs
    with st.sidebar.expander("Upload PDF"):
        uploaded_files = st.file_uploader("Drag and drop your PDFs here", accept_multiple_files=True, type=["pdf"])
        if uploaded_files:
            for uploaded_file in uploaded_files:
                with open(os.path.join("data/private", uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.write(f"Uploaded: {uploaded_file.name}")
            st.success("Files uploaded successfully!")

            # Repopulate the database
            populate_database()

    # Option to clear uploaded documents
    if st.sidebar.button("Clear uploaded documents & repopulate database"):
        clear_uploaded_documents()
        st.sidebar.success("Uploaded documents cleared and database repopulated with public data.")

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if enable_history:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response, sources = query_rag(prompt, k, similarity_threshold)
            display_response(response, sources)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "sources": sources
            })

if __name__ == "__main__":
    if not os.path.exists("data/private"):
        os.makedirs("data/private")
    main()