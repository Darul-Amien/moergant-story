import json
import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ------------------------------------------------------------------------------
# 1. KONFIGURASI AWAL & API KEY
# ------------------------------------------------------------------------------
load_dotenv()
api_key = os.getenv("XAI_API_KEY")

st.set_page_config(
    page_title="Grok Co-Writer Studio Pro",
    page_icon="✍️",
    layout="wide"
)

st.title("✍️ Grok AI Co-Writer Studio Pro")
st.caption("Studio Penulis Cerita Pribadi berbasis Grok API (Model: grok-3)")

if not api_key:
    st.error("API Key belum dikonfigurasi di file .env. Pastikan baris 'XAI_API_KEY=kunci_anda' sudah ada.")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.x.ai/v1",
)

HISTORY_FILE = "chat_history.json"
CONFIG_FILE = "story_config.json"

# ------------------------------------------------------------------------------
# 2. INSTRUKSI PERAN UTAMA (SYSTEM PROMPT)
# ------------------------------------------------------------------------------
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Kamu adalah seorang rekan penulis (co-writer) cerita fiksi profesional, kreatif, dan multi-bahasa. "
        "Tugasmu adalah membantu pengguna menyusun, mengembangkan, dan melanjutkan alur cerita dengan aturan utama berikut:\n\n"
        "1. GAYA PENULISAN & TONASI (WRITING STYLE): Patuhi instruksi gaya penulisan, nada narasi, dan ritme kalimat "
        "sesuai parameter gaya yang diberikan pengguna.\n"
        "2. KONSISTENSI KARAKTER (CHARACTER VOICE): Patuhi profil karakter yang tersimpan dalam sistem. Setiap tokoh "
        "harus memiliki gaya bicara, diksi, dan pola pikir yang khas.\n"
        "3. SETTING, LOKASI & JARAK REALISTIS: Patuhi detail lokasi yang tersimpan. Gunakan estimasi jarak geografis "
        "dan waktu tempuh nyata sesuai moda transportasi yang digunakan.\n"
        "4. BAHASA DAERAH & GLOSARIUM: Patuhi daftar glosarium kosa kata daerah yang tersimpan dalam sistem.\n"
        "5. PERGANTIAN POV (SUDUT PANDANG): Jika terjadi pergantian POV, berikan penanda jelas "
        "(contoh: '--- POV: [Nama Tokoh] ---') dan sesuaikan persepsi internalnya.\n"
        "6. DINAMIKA NARASI: Gunakan teknik 'show, don't tell' dan selaraskan dengan konteks alur cerita sebelumnya."
    )
}

# ------------------------------------------------------------------------------
# 3. FUNGSI MANAJEMEN MEMORI PERMANEN (JSON)
# ------------------------------------------------------------------------------
def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_chat_history(messages):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def load_story_config():
    """Memuat data Karakter, Style, Setting, dan Glosarium dari file JSON."""
    default_config = {
        "style": "* Tonasi: Emosional, Intim, & Mendalam\n* Pilihan Kata: Mengalir, deskriptif panca indera, mengutamakan emosi internal tokoh.\n* Ritme Kalimat: Bervariasi (kombinasi kalimat pendek saat intens dan panjang saat deskriptif).",
        "characters": "1. Marno (POV Utama): Logis, tenang, bicara halus.\n2. Bambang: Impulsif, ceplas-ceplos, humoris.",
        "settings": "* Lokasi Utama: Desa Sukamaju, Kabupaten Hulu Sungai\n* Tempat Spesifik: Pos Ronda RT 03, Hutan Pinus Pinggir Desa\n* Waktu/Suasana: Malam hari, gerimis, penerangan minim",
        "glossary": "* Kula / Inyong = Saya\n* Mangan = Makan\n* Bledheg = Petir"
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                # Pastikan key 'style' dan 'settings' ada jika memuat file lama
                if "style" not in config_data:
                    config_data["style"] = default_config["style"]
                if "settings" not in config_data:
                    config_data["settings"] = default_config["settings"]
                return config_data
        except Exception:
            return default_config
    return default_config

def save_story_config(style, characters, settings, glossary):
    """Menyimpan data Karakter, Style, Setting, dan Glosarium ke file JSON."""
    config = {
        "style": style,
        "characters": characters,
        "settings": settings,
        "glossary": glossary
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# Inisialisasi State
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

if "story_config" not in st.session_state:
    st.session_state.story_config = load_story_config()

if "quick_action" not in st.session_state:
    st.session_state.quick_action = None

# ------------------------------------------------------------------------------
# 4. BILAH SAMPING (SIDEBAR) & EDIT PENGATURAN CERITA
# ------------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Pengaturan Penulisan")
    
    creativity = st.slider(
        "Tingkat Kreativitas (Temperature)",
        min_value=0.1, max_value=1.0, value=0.7, step=0.05
    )

    st.markdown("---")
    
    # --- FITUR EDIT STYLE, KARAKTER, SETTING & GLOSARIUM ---
    with st.expander("🎨 Gaya Penulisan & Tonasi", expanded=False):
        style_input = st.text_area(
            "Panduan Gaya Penulisan:",
            value=st.session_state.story_config.get("style", ""),
            height=120,
            help="Tentukan suasana (mood), ritme narasi, atau diksi spesifik yang diinginkan di sini."
        )

    with st.expander("👤 Manajemen Karakter / Tokoh", expanded=False):
        characters_input = st.text_area(
            "Daftar & Profil Karakter:",
            value=st.session_state.story_config.get("characters", ""),
            height=120,
            help="Edit nama tokoh, sifat, dan gaya bicaranya di sini."
        )

    with st.expander("🏞️ Setting & Lokasi Cerita", expanded=False):
        settings_input = st.text_area(
            "Detail Latar Tempat & Suasana:",
            value=st.session_state.story_config.get("settings", ""),
            height=120,
            help="Edit nama daerah, kota, tempat spesifik, waktu, atau era cerita di sini."
        )

    with st.expander("📖 Glosarium Bahasa Daerah", expanded=False):
        glossary_input = st.text_area(
            "Daftar Kosa Kata Daerah:",
            value=st.session_state.story_config.get("glossary", ""),
            height=120,
            help="Edit kosa kata bahasa daerah beserta artinya di sini."
        )

    # Simpan Otomatis jika Ada Perubahan Teks
    if (style_input != st.session_state.story_config.get("style") or
        characters_input != st.session_state.story_config.get("characters") or 
        settings_input != st.session_state.story_config.get("settings") or
        glossary_input != st.session_state.story_config.get("glossary")):
        
        st.session_state.story_config["style"] = style_input
        st.session_state.story_config["characters"] = characters_input
        st.session_state.story_config["settings"] = settings_input
        st.session_state.story_config["glossary"] = glossary_input
        
        save_story_config(style_input, characters_input, settings_input, glossary_input)
        st.toast("💾 Pengaturan cerita berhasil diperbarui!", icon="✅")

    st.markdown("---")
    st.subheader("🚀 Aksi Cepat Penulisan")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Lanjutkan"):
            st.session_state.quick_action = "Lanjutkan alur cerita dari bagian terakhir secara alami dan mengalir."
        if st.button("🏞️ Perdalam Latar"):
            st.session_state.quick_action = "Gambarkan latar suasana, lokasi, dan sensorik panca indera pada adegan terakhir secara lebih detail."
    
    with col2:
        if st.button("⚡ Plot Twist"):
            st.session_state.quick_action = "Berikan sebuah kejutan alur (plot twist) menarik yang tak terduga pada adegan ini."
        if st.button("🔄 Ganti POV"):
            st.session_state.quick_action = "Pindahkan alih sudut pandang (POV) ke karakter lain dalam adegan ini, dan tunjukkan persepsi serta sudut pandang internalnya."

    if st.button("🗣️ Pertebal Bahasa Daerah"):
        st.session_state.quick_action = "Lanjutkan adegan ini dengan meningkatkan porsi penggunaan kosa kata/dialek bahasa daerah sesuai glosarium."

    st.markdown("---")
    st.subheader("💾 Manajemen Naskah")
    
    full_story_text = "\n\n".join([
        f"[{'PENULIS' if m['role'] == 'user' else 'GROK'}]\n{m['content']}"
        for m in st.session_state.messages
    ])
    
    st.download_button(
        label="📥 Download Naskah (.txt)",
        data=full_story_text,
        file_name="naskah_cerita.txt",
        mime="text/plain",
        use_container_width=True
    )
    
    if st.button("🗑️ Hapus & Mulai Cerita Baru", type="primary", use_container_width=True):
        st.session_state.messages = []
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        st.success("Naskah cerita telah dibersihkan!")
        st.rerun()

# ------------------------------------------------------------------------------
# 5. TAMPILAN RIWAYAT PERCAKAPAN
# ------------------------------------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ------------------------------------------------------------------------------
# 6. PENANGANAN INPUT PENGGUNA & GENERASI CERITA
# ------------------------------------------------------------------------------
user_input = st.chat_input("Ketik ide cerita atau kelanjutan kisah di sini...")

if st.session_state.quick_action:
    prompt = st.session_state.quick_action
    st.session_state.quick_action = None
elif user_input:
    prompt = user_input
else:
    prompt = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # Menyusun Instruksi Konteks Dinamika (Membawa Data Style, Karakter, Setting, & Glosarium Terbaru)
            context_instruction = {
                "role": "system",
                "content": (
                    f"--- PANDUAN GAYA PENULISAN AKTIF ---\n{st.session_state.story_config.get('style', '')}\n\n"
                    f"--- PROFIL KARAKTER AKTIF ---\n{st.session_state.story_config.get('characters', '')}\n\n"
                    f"--- SETTING & LOKASI CERITA AKTIF ---\n{st.session_state.story_config.get('settings', '')}\n\n"
                    f"--- GLOSARIUM BAHASA DAERAH AKTIF ---\n{st.session_state.story_config.get('glossary', '')}"
                )
            }

            # Menyusun Payload Lengkap untuk Grok API
            api_messages = [SYSTEM_PROMPT, context_instruction] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]

            response = client.chat.completions.create(
                model="grok-3",
                messages=api_messages,
                temperature=creativity,
                stream=True
            )

            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_chat_history(st.session_state.messages)
            st.rerun()

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memanggil Grok API: {e}")
