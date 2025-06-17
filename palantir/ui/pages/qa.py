import requests
import streamlit as st

API_URL = "http://localhost:8000/qa"


def render_page():
    st.title("Retrieval QA")
    question = st.text_input("Question")
    if st.button("Ask") and question:
        with st.spinner("Querying..."):
            resp = requests.post(API_URL, json={"question": question})
            if resp.status_code == 200:
                data = resp.json()
                st.write(data.get("answer"))
                if data.get("prediction") is not None:
                    st.write(f"Prediction: {data['prediction']}")
            else:
                st.error("Request failed")
