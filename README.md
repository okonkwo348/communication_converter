# Multimodal AI Studio — communication_converter

A compact Streamlit studio for quick exploration of speech and vision conversion pipelines: speech-to-text (Whisper), text-to-speech (gTTS or OpenAI TTS), and OCR (Tesseract). Designed to run on Linux (Ubuntu/Debian and Fedora) and focused on fast local experimentation and demos.

- Primary use: transcribe audio, synthesize speech, extract text from images, and generate downloadable audio/text outputs.
- Intended audience: developers and researchers who want a small, self-contained demo app for multimodal input/output pipelines.

---

## Features

- Speech-to-text using OpenAI Whisper (via the OpenAI SDK).
- Text-to-speech using:
  - gTTS (free, no API key) or
  - OpenAI TTS (requires OpenAI API key).
- OCR using Tesseract (via pytesseract + Pillow).
- Streamlit UI with theme options, session history (last 5 operations), and download buttons for transcripts/audio.
- Graceful handling and UI messages when optional libraries or system binaries are missing.

---

## Quickstart (shortest path)

1. Install system dependencies (choose one set):

   Ubuntu / Debian:
   ```bash
   sudo apt update
   sudo apt install -y tesseract-ocr ffmpeg
   # optional: dev headers
   sudo apt install -y libtesseract-dev
   ```

   Fedora:
   ```bash
   sudo dnf install -y tesseract ffmpeg
   # optional: dev headers
   sudo dnf install -y tesseract-devel
   ```

   Verify:
   ```bash
   tesseract --version
   ffmpeg -version
   ```

2. Clone, create venv, install Python deps:
   ```bash
   git clone https://github.com/okonkwo348/communication_converter.git
   cd communication_converter
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Start the app:
   ```bash
   streamlit run app.py
   ```

4. Open the Streamlit UI displayed in your terminal (typically http://localhost:8501). Enter your OpenAI API key in the sidebar if you want Whisper or OpenAI TTS functionality (or leave it empty to use gTTS for TTS).

---

## Usage overview

- Audio Lab (🎙️):
  - Upload an audio file (mp3, wav, m4a, ogg, webm).
  - Click "Transcribe with Whisper" to produce a transcript (requires OpenAI API key and the `openai` package).
  - Enter text into the TTS box and click "Generate Speech" to get an MP3 (gTTS or OpenAI TTS).
  - Download transcript or generated MP3 via download buttons.

- Vision Lab (👁️):
  - Upload an image (png, jpg, jpeg, bmp, tiff).
  - Click "Extract Text (OCR)" to run Tesseract and view extracted text.
  - Click "Convert Extracted Text to Speech" to synthesize a narration audio file.
  - Download extracted text or narration MP3.

- Session History (📜):
  - Rolling log of the last five operations, including timestamps and short previews.
  - Option to clear history.

---

## Configuration & environment variables

- OpenAI API key:
  - You can enter it directly in the Streamlit sidebar (stored only in the current session).
  - Or export in your shell (useful for local development):
    ```bash
    export OPENAI_API_KEY="sk-..."
    ```
  - Note: the app uses the OpenAI Python SDK if installed; otherwise it shows an explanatory UI error.

- Tesseract binary:
  - The app expects the tesseract binary at `/usr/bin/tesseract` (standard on many Linux distros). If installed elsewhere, update the path in `app.py` where it sets `pytesseract.pytesseract.tesseract_cmd`.

---

## Dependencies

See `requirements.txt`. Main Python packages:
- streamlit >= 1.36.0 — UI
- openai >= 1.35.0 — Whisper & OpenAI TTS client
- gTTS >= 2.5.1 — fallback/free TTS
- pytesseract >= 0.3.10, Pillow >= 10.x — OCR
- python-dotenv >= 1.0.1 — optional .env support

Also requires system binaries:
- tesseract (Tesseract OCR)
- ffmpeg (used for certain audio handling on some platforms)

---

## Troubleshooting

- "OpenAI SDK not installed" / ImportError:
  - pip install openai
  - If you don't want OpenAI features, you can still use gTTS for TTS.

- "Tesseract not found" or OCR returns nothing:
  - Ensure the tesseract binary is installed: `tesseract --version`.
  - On Debian/Ubuntu: `sudo apt install tesseract-ocr`
  - If tesseract is installed at a non-standard location, edit app.py to set `pytesseract.pytesseract.tesseract_cmd = "/path/to/tesseract"`.

- Audio generation errors:
  - For gTTS: ensure `gtts` is installed and you have network access (gTTS uses Google TTS).
  - For OpenAI TTS: make sure the OpenAI API key is provided and valid.

- Streamlit errors or UI shows missing packages:
  - Read the sidebar system status; it reports availability for OpenAI SDK, gTTS, and Tesseract.
  - Re-run `pip install -r requirements.txt` inside your virtual environment.

---

## Development notes

- Main application entry: `app.py` — Streamlit single-file app.
- UI contains small theming engine (CSS injection) and helper functions for:
  - `transcribe_audio_whisper` — calls OpenAI audio transcription.
  - `synthesize_speech` — uses either gTTS or OpenAI TTS depending on sidebar choice.
  - `extract_text_from_image` — uses pytesseract and Pillow.
- The app keeps a short in-memory session history via `st.session_state`.

If you plan to extend the project:
- Add modular structure (e.g., `src/` with `stt.py`, `tts.py`, `ocr.py`) for easier unit testing.
- Add automated tests around helper functions by isolating logic from Streamlit UI.
- Add CI with pinned dependency checks and linting (e.g., pre-commit, flake8).

---

## Security & privacy

- Do NOT commit API keys to the repository.
- The app stores the OpenAI key only in the Streamlit session input; if you set it via environment variables, the app may read them in future development (consider using `.env` with python-dotenv for local dev).
- Transcribed text and uploaded files are handled locally in the session and not persisted by the repository. If you deploy, verify any deployment provider's privacy/retention policies.

---

## Contributing

Contributions welcome. Suggestions:
- Add tests and CI.
- Split app into modules for easier maintenance.
- Add a Dockerfile for consistent environment reproduction.
- Add a license (this repository currently has no license file).

When opening PRs:
- Provide a short description of the change and a reproduction/test case.
- Keep UI changes consistent with existing theming.

---

## License

No license specified. If you want to permit reuse, consider adding an OSI-approved license such as MIT, Apache-2.0, or GPL-3.0. Example: create a `LICENSE` file with the chosen license text.

---

## Contact

Repository owner: @okonkwo348  
For issues, open a GitHub Issue with "bug" or "feature" tags and include steps to reproduce and environment details.
