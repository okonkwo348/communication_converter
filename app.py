"""
================================================================================
 MULTIMODAL AI STUDIO — app.py
 Streamlit application: Speech-to-Text, Text-to-Speech, and OCR (Vision)
 Optimized for Linux (Ubuntu/Debian & Fedora) deployment.
================================================================================

--------------------------------------------------------------------------------
 LINUX SYSTEM DEPENDENCIES (run these in your terminal BEFORE launching the app)
--------------------------------------------------------------------------------

# ---- Ubuntu / Debian (apt) -----------------------------------------------
# sudo apt update
# sudo apt install -y tesseract-ocr ffmpeg
# sudo apt install -y libtesseract-dev   # optional, dev headers
#
# Verify installation:
# tesseract --version
# ffmpeg -version

# ---- Fedora (dnf) ----------------------------------------------------------
# sudo dnf install -y tesseract ffmpeg
# sudo dnf install -y tesseract-devel    # optional, dev headers
#
# Verify installation:
# tesseract --version
# ffmpeg -version

--------------------------------------------------------------------------------
 requirements.txt  (create this file alongside app.py)
--------------------------------------------------------------------------------
# streamlit>=1.36.0
# openai>=1.35.0
# gTTS>=2.5.1
# pytesseract>=0.3.10
# Pillow>=10.3.0
# python-dotenv>=1.0.1

--------------------------------------------------------------------------------
 RUN THE APP
--------------------------------------------------------------------------------
# streamlit run app.py

================================================================================
"""

import os
import io
import time
import base64
import tempfile
import datetime as dt

import streamlit as st

# --- Third-party libraries (each import is guarded so the app degrades
#     gracefully with a clear UI error instead of a hard crash on Linux
#     boxes that are missing a system/python dependency). ---------------------
try:
    from openai import OpenAI
    OPENAI_SDK_AVAILABLE = True
except Exception:
    OPENAI_SDK_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except Exception:
    GTTS_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    # Standard install path for tesseract binary on most Linux distros
    # (apt / dnf both drop the binary at /usr/bin/tesseract by default).
    _default_tesseract_path = "/usr/bin/tesseract"
    if os.path.exists(_default_tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = _default_tesseract_path
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


# ==============================================================================
# PAGE CONFIG
# ==============================================================================
st.set_page_config(
    page_title="Multimodal AI Studio",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
def init_state():
    defaults = {
        "history": [],                 # rolling log of last 5 operations
        "theme": "🌌 Cyberpunk",
        "openai_api_key": "",
        "last_transcript": "",
        "last_ocr_text": "",
        "last_tts_audio": None,
        "last_tts_ocr_audio": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_state()


def add_to_history(tool_type: str, data_preview: str):
    """Append an operation to the rolling history log, keeping only the last 5."""
    entry = {
        "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tool": tool_type,
        "preview": (data_preview[:120] + "…") if len(data_preview) > 120 else data_preview,
    }
    st.session_state.history.append(entry)
    # Drop oldest entry once we exceed 5 records
    if len(st.session_state.history) > 5:
        st.session_state.history = st.session_state.history[-5:]


# ==============================================================================
# THEME ENGINE — CSS INJECTION
# ==============================================================================
THEMES = {
    "🌌 Cyberpunk": """
        <style>
        html, body, [data-testid="stAppViewContainer"], .main {
            background-color: #000000 !important;
            color: #E0E0FF !important;
        }
        [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
        [data-testid="stSidebar"] {
            background-color: #0a0a0f !important;
            border-right: 1px solid #8A2BE2;
        }
        h1, h2, h3 {
            color: #8A2BE2 !important;
            text-shadow: 0 0 8px #8A2BE2, 0 0 18px rgba(138,43,226,0.6);
            font-weight: 800 !important;
        }
        h4, h5, h6, label, p, span, div { color: #E0E0FF; }
        .stButton>button {
            background: linear-gradient(135deg, #0d0d14, #1a0a2e);
            color: #00F0FF !important;
            border: 1px solid #00F0FF;
            border-radius: 8px;
            box-shadow: 0 0 6px rgba(0,240,255,0.5);
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            box-shadow: 0 0 18px rgba(0,240,255,0.9), 0 0 30px rgba(138,43,226,0.5);
            border-color: #8A2BE2;
            transform: translateY(-1px);
        }
        [data-testid="stFileUploader"], .stTextInput>div>div, .stTextArea textarea {
            background-color: #0d0d14 !important;
            border: 1px solid #8A2BE2 !important;
            border-radius: 8px;
            color: #E0E0FF !important;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 6px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #0d0d14;
            border: 1px solid #8A2BE2;
            border-radius: 8px 8px 0 0;
            color: #E0E0FF;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1a0a2e;
            color: #00F0FF !important;
            box-shadow: 0 -2px 10px rgba(0,240,255,0.4);
        }
        .ai-card {
            background-color: #0a0a12;
            border: 1px solid #8A2BE2;
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 0 14px rgba(138,43,226,0.25);
        }
        </style>
    """,
    "🖤 Minimal Dark": """
        <style>
        html, body, [data-testid="stAppViewContainer"], .main {
            background-color: #1E1E24 !important;
            color: #EDEDED !important;
        }
        [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
        [data-testid="stSidebar"] {
            background-color: #17171C !important;
            border-right: 1px solid #33333B;
        }
        h1, h2, h3 {
            color: #FAFAFA !important;
            font-weight: 700 !important;
            letter-spacing: 0.3px;
        }
        h4, h5, h6, label, p, span, div { color: #D8D8DC; }
        .stButton>button {
            background-color: #2A2A32;
            color: #FFFFFF !important;
            border: 1px solid #FFFFFF;
            border-radius: 6px;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            background-color: #35353E;
            border-color: #9E9EF0;
        }
        [data-testid="stFileUploader"], .stTextInput>div>div, .stTextArea textarea {
            background-color: #26262E !important;
            border: 1px solid #3A3A44 !important;
            border-radius: 6px;
            color: #EDEDED !important;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #26262E;
            border: 1px solid #3A3A44;
            color: #D8D8DC;
        }
        .stTabs [aria-selected="true"] {
            background-color: #33333D;
            color: #FFFFFF !important;
        }
        .ai-card {
            background-color: #24242C;
            border: 1px solid #3A3A44;
            border-radius: 10px;
            padding: 18px;
        }
        </style>
    """,
    "☀️ Light Mode": """
        <style>
        html, body, [data-testid="stAppViewContainer"], .main {
            background-color: #FAFAF7 !important;
            color: #1B1B1F !important;
        }
        [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
        [data-testid="stSidebar"] {
            background-color: #F1F1EC !important;
            border-right: 1px solid #D8D8D0;
        }
        h1, h2, h3 {
            color: #1B3A8C !important;
            font-weight: 800 !important;
        }
        h4, h5, h6, label, p, span, div { color: #2A2A2E; }
        .stButton>button {
            background-color: #FFFFFF;
            color: #1B3A8C !important;
            border: 1px solid #1B3A8C;
            border-radius: 6px;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            background-color: #1B3A8C;
            color: #FFFFFF !important;
        }
        [data-testid="stFileUploader"], .stTextInput>div>div, .stTextArea textarea {
            background-color: #FFFFFF !important;
            border: 1px solid #C9C9C0 !important;
            border-radius: 6px;
            color: #1B1B1F !important;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #FFFFFF;
            border: 1px solid #D8D8D0;
            color: #2A2A2E;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1B3A8C;
            color: #FFFFFF !important;
        }
        .ai-card {
            background-color: #FFFFFF;
            border: 1px solid #D8D8D0;
            border-radius: 10px;
            padding: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        </style>
    """,
}


def apply_theme(theme_name: str):
    st.markdown(THEMES.get(theme_name, THEMES["🌌 Cyberpunk"]), unsafe_allow_html=True)


# ==============================================================================
# SIDEBAR — THEME + CONFIG
# ==============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Studio Settings")

    theme_choice = st.selectbox(
        "🎨 Interface Theme",
        options=list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme),
    )
    st.session_state.theme = theme_choice

    st.divider()

    st.markdown("### 🔑 API Configuration")
    api_key_input = st.text_input(
        "OpenAI API Key",
        value=st.session_state.openai_api_key,
        type="password",
        help="Required for Whisper transcription and OpenAI TTS. Stored only in this session.",
    )
    st.session_state.openai_api_key = api_key_input

    tts_engine = st.radio(
        "🔊 Text-to-Speech Engine",
        options=["gTTS (Free, no key needed)", "OpenAI TTS (requires API key)"],
        index=0,
    )

    st.divider()
    st.markdown("### 🖥️ System Status")
    st.write(f"OpenAI SDK: {'✅ Available' if OPENAI_SDK_AVAILABLE else '❌ Not installed'}")
    st.write(f"gTTS: {'✅ Available' if GTTS_AVAILABLE else '❌ Not installed'}")
    st.write(f"Tesseract OCR: {'✅ Available' if OCR_AVAILABLE else '❌ Not installed'}")

    st.caption(
        "Install missing system packages with the apt/dnf commands documented "
        "at the top of app.py, then `pip install -r requirements.txt`."
    )

apply_theme(st.session_state.theme)


# ==============================================================================
# HELPER FUNCTIONS — AI PIPELINES
# ==============================================================================
def get_openai_client():
    """Return an OpenAI client instance, or None if unavailable/misconfigured."""
    if not OPENAI_SDK_AVAILABLE:
        st.error("The `openai` package is not installed. Run: pip install openai")
        return None
    if not st.session_state.openai_api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
        return None
    try:
        return OpenAI(api_key=st.session_state.openai_api_key)
    except Exception as e:
        st.error(f"Failed to initialize OpenAI client: {e}")
        return None


def transcribe_audio_whisper(audio_bytes: bytes, filename: str = "audio.wav"):
    """Send audio bytes to OpenAI Whisper API and return the transcript text."""
    client = get_openai_client()
    if client is None:
        return None
    tmp_path = None
    try:
        suffix = os.path.splitext(filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        with open(tmp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
            )
        return transcript.text
    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def synthesize_speech(text: str, engine_choice: str, voice: str = "alloy", lang: str = "en"):
    """Generate speech audio bytes (MP3) from text using the selected engine."""
    if not text or not text.strip():
        st.warning("There is no text to synthesize.")
        return None

    try:
        if engine_choice.startswith("gTTS"):
            if not GTTS_AVAILABLE:
                st.error("gTTS is not installed. Run: pip install gTTS")
                return None
            buf = io.BytesIO()
            tts = gTTS(text=text, lang=lang)
            tts.write_to_fp(buf)
            buf.seek(0)
            return buf.read()

        else:  # OpenAI TTS
            client = get_openai_client()
            if client is None:
                return None
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
            )
            return response.content

    except Exception as e:
        st.error(f"Speech synthesis failed: {e}")
        return None


def extract_text_from_image(image_bytes: bytes):
    """Run Tesseract OCR on an uploaded image and return the extracted text."""
    if not OCR_AVAILABLE:
        st.error(
            "OCR dependencies missing. Install with:\n"
            "  Ubuntu/Debian → sudo apt install tesseract-ocr\n"
            "  Fedora        → sudo dnf install tesseract\n"
            "  then: pip install pytesseract Pillow"
        )
        return None, None
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("RGB")
        text = pytesseract.image_to_string(image)
        return text.strip(), image
    except Exception as e:
        st.error(f"OCR extraction failed: {e}")
        return None, None


def audio_download_button(audio_bytes: bytes, label: str, filename: str, key: str):
    st.download_button(
        label=label,
        data=audio_bytes,
        file_name=filename,
        mime="audio/mp3",
        key=key,
        use_container_width=True,
    )


def text_download_button(text: str, label: str, filename: str, key: str):
    st.download_button(
        label=label,
        data=text.encode("utf-8"),
        file_name=filename,
        mime="text/plain",
        key=key,
        use_container_width=True,
    )


# ==============================================================================
# HEADER
# ==============================================================================
st.title("🧠 Multimodal AI Studio")
st.caption(
    "Speech-to-Text · Text-to-Speech · OCR Vision — powered by OpenAI Whisper, "
    "gTTS/OpenAI TTS, and Tesseract OCR."
)

tab_audio, tab_vision, tab_history = st.tabs(
    ["🎙️ Audio Lab (STT / TTS)", "👁️ Vision Lab (OCR)", "📜 Session History"]
)


# ==============================================================================
# TAB 1 — AUDIO LAB (Speech-to-Text + Text-to-Speech)
# ==============================================================================
with tab_audio:
    left_col, right_col = st.columns([0.4, 0.6], gap="large")

    with left_col:
        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("🎙️ Speech → Text")
        audio_file = st.file_uploader(
            "Upload an audio file (mp3, wav, m4a, ogg)",
            type=["mp3", "wav", "m4a", "ogg", "webm"],
            key="audio_upload",
        )
        transcribe_clicked = st.button("🚀 Transcribe with Whisper", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("🔊 Text → Speech")
        tts_text_input = st.text_area(
            "Enter text to convert into speech",
            height=140,
            placeholder="Type or paste text here...",
            key="tts_text_area",
        )
        voice_choice = st.selectbox(
            "Voice (OpenAI TTS only)",
            options=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            index=0,
        )
        generate_clicked = st.button("✨ Generate Speech", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("📄 Transcription Result")

        if transcribe_clicked:
            if audio_file is None:
                st.warning("Please upload an audio file first.")
            else:
                with st.spinner("Transcribing audio with Whisper…"):
                    audio_bytes = audio_file.read()
                    result_text = transcribe_audio_whisper(audio_bytes, audio_file.name)
                if result_text:
                    st.session_state.last_transcript = result_text
                    add_to_history("STT (Whisper)", result_text)
                    st.toast("✅ Transcription ready!", icon="🎧")

        if st.session_state.last_transcript:
            st.text_area(
                "Transcript",
                value=st.session_state.last_transcript,
                height=150,
                key="transcript_display",
            )
            text_download_button(
                st.session_state.last_transcript,
                "⬇️ Download Transcript (.txt)",
                "transcript.txt",
                "download_transcript",
            )
        else:
            st.info("Your transcription will appear here.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("🎧 Generated Audio")

        if generate_clicked:
            with st.spinner("Synthesizing speech…"):
                audio_out = synthesize_speech(tts_text_input, tts_engine, voice=voice_choice)
            if audio_out:
                st.session_state.last_tts_audio = audio_out
                add_to_history("TTS", tts_text_input)
                st.toast("✅ Audio generated!", icon="🔊")

        if st.session_state.last_tts_audio:
            player_col, dl_col = st.columns([0.65, 0.35])
            with player_col:
                st.audio(st.session_state.last_tts_audio, format="audio/mp3")
            with dl_col:
                audio_download_button(
                    st.session_state.last_tts_audio,
                    "⬇️ Download MP3",
                    "generated_speech.mp3",
                    "download_tts_audio",
                )
        else:
            st.info("Your generated audio player will appear here.")
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# TAB 2 — VISION LAB (OCR)
# ==============================================================================
with tab_vision:
    left_col, right_col = st.columns([0.4, 0.6], gap="large")

    with left_col:
        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("🖼️ Upload Image")
        image_file = st.file_uploader(
            "Upload an image (png, jpg, jpeg, bmp, tiff)",
            type=["png", "jpg", "jpeg", "bmp", "tiff"],
            key="image_upload",
        )
        extract_clicked = st.button("🔍 Extract Text (OCR)", use_container_width=True)
        st.caption("Uses Tesseract OCR via `pytesseract`, configured for standard Linux paths.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("🔊 Narrate Extracted Text")
        narrate_clicked = st.button("🗣️ Convert Extracted Text to Speech", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("🖼️ Image Preview")

        if extract_clicked:
            if image_file is None:
                st.warning("Please upload an image first.")
            else:
                with st.spinner("Running OCR extraction…"):
                    img_bytes = image_file.read()
                    ocr_text, pil_image = extract_text_from_image(img_bytes)
                if ocr_text is not None and pil_image is not None:
                    st.session_state.last_ocr_text = ocr_text
                    st.session_state["_ocr_preview_bytes"] = img_bytes
                    add_to_history("OCR (Tesseract)", ocr_text or "(no text detected)")
                    st.toast("✅ Text extracted!", icon="🔍")

        if st.session_state.get("_ocr_preview_bytes"):
            st.image(
                st.session_state["_ocr_preview_bytes"],
                caption="Uploaded Image",
                use_container_width=True,
            )
        else:
            st.info("Your uploaded image preview will appear here.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("📄 Extracted Text")

        if st.session_state.last_ocr_text:
            st.text_area(
                "OCR Output",
                value=st.session_state.last_ocr_text,
                height=150,
                key="ocr_text_display",
            )
            text_download_button(
                st.session_state.last_ocr_text,
                "⬇️ Download Extracted Text (.txt)",
                "extracted_text.txt",
                "download_ocr_text",
            )
        else:
            st.info("Extracted text will appear here after running OCR.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="ai-card">', unsafe_allow_html=True)
        st.subheader("🎧 Extracted Text — Audio Narration")

        if narrate_clicked:
            if not st.session_state.last_ocr_text:
                st.warning("Extract text from an image first.")
            else:
                with st.spinner("Synthesizing narration…"):
                    narrate_audio = synthesize_speech(
                        st.session_state.last_ocr_text, tts_engine, voice=voice_choice
                    )
                if narrate_audio:
                    st.session_state.last_tts_ocr_audio = narrate_audio
                    add_to_history("TTS (OCR narration)", st.session_state.last_ocr_text)
                    st.toast("✅ Narration ready!", icon="🎧")

        if st.session_state.last_tts_ocr_audio:
            player_col, dl_col = st.columns([0.65, 0.35])
            with player_col:
                st.audio(st.session_state.last_tts_ocr_audio, format="audio/mp3")
            with dl_col:
                audio_download_button(
                    st.session_state.last_tts_ocr_audio,
                    "⬇️ Download MP3",
                    "ocr_narration.mp3",
                    "download_ocr_audio",
                )
        else:
            st.info("Narration audio player will appear here.")
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# TAB 3 — SESSION HISTORY
# ==============================================================================
with tab_history:
    st.markdown('<div class="ai-card">', unsafe_allow_html=True)
    st.subheader("📜 Last 5 Operations")

    if not st.session_state.history:
        st.info("No operations logged yet. Use the Audio or Vision labs to get started.")
    else:
        for entry in reversed(st.session_state.history):
            with st.container():
                c1, c2, c3 = st.columns([0.22, 0.18, 0.60])
                c1.markdown(f"🕒 **{entry['timestamp']}**")
                c2.markdown(f"🔧 `{entry['tool']}`")
                c3.markdown(f"📝 {entry['preview']}")
                st.divider()

        if st.button("🗑️ Clear History", use_container_width=False):
            st.session_state.history = []
            st.toast("History cleared.", icon="🗑️")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
st.caption(
    "Multimodal AI Studio · Streamlit + OpenAI Whisper/TTS + Tesseract OCR · "
    "Built for Linux deployment (Ubuntu/Debian & Fedora)."
)
