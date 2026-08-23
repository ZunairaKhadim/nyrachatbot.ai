import streamlit as st
from google import genai
from google.genai import types
import json
import os
import uuid
import time
import urllib.parse
import requests
from pathlib import Path

st.set_page_config(page_title="Nyra", page_icon="💠", layout="centered")

st.markdown("""
<style>
.stButton>button {
    border-radius: 999px !important;
    padding: 0.45rem 1.1rem !important;
    border: 1px solid #E5E7EB !important;
    background: #FFFFFF !important;
    color: #111827 !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
}
.stButton>button:hover {
    background: #F3F4F6 !important;
    border-color: #D1D5DB !important;
}
section[data-testid="stSidebar"] button {
    border: none !important;
    background: transparent !important;
    text-align: left !important;
    box-shadow: none !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] button:hover {
    background: #F3F4F6 !important;
}
.brand-logo {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: linear-gradient(135deg, #2563EB, #1D4ED8);
    color: white;
    margin-right: 8px;
    vertical-align: middle;
}
.brand-logo { font-size: 1.1rem; }
.brand-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #111827;
    vertical-align: middle;
}
.welcome-wrap {
    text-align: center;
    padding-top: 3rem;
    padding-bottom: 1.5rem;
}
.welcome-logo {
    width: 64px;
    height: 64px;
    border-radius: 18px;
    background: linear-gradient(135deg, #2563EB, #1D4ED8);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 0.75rem auto;
}
.welcome-logo { font-size: 2rem; }
.welcome-wrap h2 {
    font-weight: 700;
    color: #111827;
}
</style>
""", unsafe_allow_html=True)

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
SESSIONS_FILE = str(Path(__file__).parent / "sessions.json")

IMAGE_STYLES = {
    "🖼️ Realistic": "realistic photo, high detail,",
    "🎬 Animated": "animated cartoon style, colorful,",
    "✏️ 2D": "flat 2D illustration, clean lines,",
    "🧊 3D": "3D render, soft lighting,",
}

MODES = {
    "General Assistant": "You are Nyra, a warm, friendly, upbeat AI assistant. Talk like a helpful friend. Keep answers clear, well-organized, and never robotic.",
    "Study Helper": "You are Nyra, a patient and encouraging tutor. Explain concepts step-by-step, check understanding, use simple examples, and break down complex topics for students.",
    "Creative Writer": "You are Nyra, an imaginative creative writing assistant. Help brainstorm, write stories, poems, and creative content with flair.",
    "Coding Helper": "You are Nyra, a clear and precise coding assistant. Explain code simply, give examples, and help debug step-by-step.",
}

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f)

if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()

if "current_id" not in st.session_state:
    if st.session_state.sessions:
        st.session_state.current_id = list(st.session_state.sessions.keys())[-1]
    else:
        new_id = str(uuid.uuid4())
        st.session_state.sessions[new_id] = {"title": "New Chat", "messages": []}
        st.session_state.current_id = new_id

if "user_name" not in st.session_state:
    st.session_state.user_name = "Friend"
if "mode" not in st.session_state:
    st.session_state.mode = "General Assistant"
if "image_mode" not in st.session_state:
    st.session_state.image_mode = None

current = st.session_state.sessions[st.session_state.current_id]

with st.sidebar:
    st.markdown('<span class="brand-logo">💠</span><span class="brand-title">Nyra</span>', unsafe_allow_html=True)
    st.divider()

    if st.button("🆕  New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.sessions[new_id] = {"title": "New Chat", "messages": []}
        st.session_state.current_id = new_id
        st.session_state.image_mode = None
        st.rerun()

    st.markdown("**Chats**")
    for sid, data in reversed(list(st.session_state.sessions.items())):
        label = data["title"][:26] + ("..." if len(data["title"]) > 26 else "")
        row_col1, row_col2 = st.columns([5, 1])
        with row_col1:
            if st.button(label, key=sid, use_container_width=True):
                st.session_state.current_id = sid
                st.rerun()
        with row_col2:
            if st.button("🗑", key=f"del_{sid}"):
                del st.session_state.sessions[sid]
                save_sessions(st.session_state.sessions)
                if st.session_state.current_id == sid:
                    if st.session_state.sessions:
                        st.session_state.current_id = list(st.session_state.sessions.keys())[-1]
                    else:
                        new_id = str(uuid.uuid4())
                        st.session_state.sessions[new_id] = {"title": "New Chat", "messages": []}
                        st.session_state.current_id = new_id
                st.rerun()

    st.divider()
    with st.expander("⚙️ Settings"):
        st.session_state.user_name = st.text_input("Your name", value=st.session_state.user_name)
        st.session_state.mode = st.selectbox("Mode", list(MODES.keys()), index=list(MODES.keys()).index(st.session_state.mode))

    st.divider()
    st.caption("Built with Streamlit + Gemini API")

if not current["messages"]:
    st.markdown(f"""
    <div class="welcome-wrap">
        <div class="welcome-logo">💠</div>
        <h2>How can I help you, {st.session_state.user_name}?</h2>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    starter = None
    with col1:
        if st.button("Explain quantum physics simply", use_container_width=True):
            starter = "Explain quantum physics simply"
        if st.button("Help me study for an exam", use_container_width=True):
            starter = "Help me study for an exam"
    with col2:
        if st.button("Give me 3 productivity tips", use_container_width=True):
            starter = "Give me 3 productivity tips"
        if st.button("Explain a hard topic simply", use_container_width=True):
            starter = "Explain a hard topic simply"
    if starter:
        st.session_state.pending_prompt = starter
        st.rerun()
else:
    st.markdown('<span class="brand-logo">💠</span><span class="brand-title">Chat with Nyra</span>', unsafe_allow_html=True)

for msg in current["messages"]:
    avatar = "🧑" if msg["role"] == "user" else "💠"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if "image_url" in msg:
            st.image(msg["image_url"])

st.markdown("<br>", unsafe_allow_html=True)
style_cols = st.columns(len(IMAGE_STYLES) + 1)
with style_cols[0]:
    if st.button("💬 Chat", use_container_width=True,
                 type="primary" if st.session_state.image_mode is None else "secondary"):
        st.session_state.image_mode = None
        st.rerun()
for i, style_name in enumerate(IMAGE_STYLES.keys()):
    with style_cols[i + 1]:
        if st.button(style_name, use_container_width=True,
                     type="primary" if st.session_state.image_mode == style_name else "secondary"):
            st.session_state.image_mode = style_name
            st.rerun()

if st.session_state.image_mode:
    placeholder_text = f"Describe the {st.session_state.image_mode.split(' ', 1)[1].lower()} image you want..."
else:
    placeholder_text = "Write your message..."

typed_prompt = st.chat_input(placeholder_text)
prompt = typed_prompt or st.session_state.pop("pending_prompt", None)

def generate_title(user_msg):
    try:
        title_resp = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=f'In 4 words or fewer, write a short descriptive title for a chat that starts with this message: "{user_msg}". Respond with ONLY the title text itself, nothing else.'
        )
        clean_title = title_resp.text.strip()
        clean_title = clean_title.strip('"').strip("'").strip(".").strip()
        return clean_title[:40] if clean_title else user_msg[:40]
    except Exception:
        return user_msg[:40]

if prompt:
    is_first_message = (current["title"] == "New Chat")

    current["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    if is_first_message:
        current["title"] = generate_title(prompt)

    if st.session_state.image_mode:
        style_prefix = IMAGE_STYLES[st.session_state.image_mode]
        full_prompt = f"{style_prefix} {prompt}"
        encoded = urllib.parse.quote(full_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true"
        with st.chat_message("assistant", avatar="💠"):
            with st.spinner("Nyra is creating your image..."):
                try:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    resp = requests.get(image_url, headers=headers, timeout=45)
                    resp.raise_for_status()
                    img_bytes = resp.content
                    caption = f"Here's your image of *{prompt}*:"
                    st.markdown(caption)
                    st.image(img_bytes)
                    st.download_button(
                        "⬇️ Download image",
                        img_bytes,
                        file_name="image.png",
                        mime="image/png",
                        key=f"dl_{len(current['messages'])}"
                    )
                    current["messages"].append({
                        "role": "assistant",
                        "content": caption,
                        "image_url": image_url
                    })
                except Exception as e:
                    err = f"Sorry, I couldn't generate that image right now: {e}"
                    st.markdown(err)
                    current["messages"].append({"role": "assistant", "content": err})
        save_sessions(st.session_state.sessions)
    else:
        with st.chat_message("assistant", avatar="💠"):
            placeholder = st.empty()
            full_reply = ""
            try:
                history = [
                    types.Content(role="user" if m["role"] == "user" else "model", parts=[types.Part(text=m["content"])])
                    for m in current["messages"] if "image_url" not in m
                ]
                stream = client.models.generate_content_stream(
                    model="gemini-3.6-flash",
                    contents=history,
                    config=types.GenerateContentConfig(system_instruction=MODES[st.session_state.mode])
                )
                word_buffer = 0
                for chunk in stream:
                    if chunk.text:
                        for word in chunk.text.split(" "):
                            full_reply += word + " "
                            word_buffer += 1
                            if word_buffer >= 4:
                                placeholder.markdown(full_reply + "▌")
                                word_buffer = 0
                                time.sleep(0.02)
                placeholder.markdown(full_reply)
            except Exception as e:
                full_reply = f"Something went wrong: {e}"
                placeholder.markdown(full_reply)

        current["messages"].append({"role": "assistant", "content": full_reply})
        save_sessions(st.session_state.sessions)