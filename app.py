import os
import streamlit as st
from openai import OpenAI

# 1. Konfigurasi Halaman untuk Tampilan HP
st.set_page_config(
    page_title="Studio Cerita Fiksi",
    page_icon="✍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS untuk optimasi layar HP
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .stChatMessage {
        font-size: 15px;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Ambil API Key dari Streamlit Secrets (Cloud Environment)
api_key = st.secrets.get("XAI_API_KEY", "")

if not api_key:
    st.error("API Key xAI tidak ditemukan. Harap tambahkan XAI_API_KEY di menu Secrets Streamlit Community Cloud.")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.x.ai/v1"
)

# 3. Sidebar Konfigurasi
with st.sidebar:
    st.header("⚙️ Pengaturan Cerita")
    temperature = st.slider("Tingkat Kreativitas Narasi", 0.0, 1.0, 0.7, 0.05)
    
    system_instruction = st.text_area(
        "Panduan AI (System Prompt)",
        value=(
            "Kamu adalah rekan penulis fiksi kreatif profesional. Fokusmu adalah menyusun cerita fiksi realistis "
            "dengan tema dewasa/dewasa muda. Tulis narasi dengan deskripsi yang mendalam, dialog yang alami, "
            "perkembangan emosi karakter yang masuk akal, serta suasana latar yang hidup."
        ),
        height=150
    )
    
    if st.button("Hapus Riwayat Chat"):
        st.session_state.messages = []
        st.rerun()

# 4. Pengelolaan Riwayat Percakapan
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("✍️ Studio Cerita Fiksi")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Input Pesan & Respon Streaming
if user_input := st.chat_input("Tulis ide, dialog, atau kelanjutan cerita..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    api_messages = [{"role": "system", "content": system_instruction}]
    for msg in st.session_state.messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            stream = client.chat.completions.create(
                model="grok-4.7",
                messages=api_messages,
                temperature=temperature,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Terjadi kesalahan saat menghubungkan ke API: {e}")
