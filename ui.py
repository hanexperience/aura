import streamlit as st
from twilio.rest import Client
import uuid
import random
import time
import json
import os

# ─────────────────────────────────────────────
# 1. TWILIO CREDENTIALS
# ─────────────────────────────────────────────
TWILIO_SID   = "AC9b4adfaf857b71fa747eb912451d1d7e"
TWILIO_TOKEN = "f6c2cb16f78b43c758959600b91ded5b"
TWILIO_FROM  = "whatsapp:+15559296253"

try:
    twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
except Exception:
    twilio_client = None

# ─────────────────────────────────────────────
# 2. LIBRARY IMPORT HELPER
# ─────────────────────────────────────────────
LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "nexus_cue_library.json")

def load_library_into_scenes(path: str) -> dict:
    """
    Reads nexus_cue_library.json and converts it to the internal
    scenes dict: { scene_name: { beat_name: [ cue_dict, … ] } }
    """
    with open(path, "r", encoding="utf-8") as f:
        lib = json.load(f)

    scenes = {}
    for scene in lib.get("scenes", []):
        scene_name = scene["name"]
        scenes[scene_name] = {}
        for beat in scene.get("beats", []):
            beat_name = beat["name"]
            cues = []
            for cue in beat.get("cues", []):
                cues.append({
                    "id":      cue.get("id", str(uuid.uuid4())),
                    "label":   cue.get("label", ""),
                    "text":    cue.get("text", ""),
                    "mode":    cue.get("mode", "Subtext"),
                    "targets": cue.get("targets", []),
                })
            scenes[scene_name][beat_name] = cues
    return scenes

PHASE_LABELS = {
    "Scene 1: Arrival":         ("PHASE 1 · EXPOSURE",   "#8b7355"),
    "Scene 2: The Reason":      ("PHASE 1 · EXPOSURE",   "#8b7355"),
    "Scene 3: The Forgetting":  ("PHASE 2 · FORGETTING", "#5a7d6e"),
    "Scene 4: The Integration": ("PHASE 3 · INTEGRATION","#6e7a9e"),
    "Scene 5: Rehearsal Tools": ("REHEARSAL ONLY",        "#666666"),
}

def phase_colour(scene_name: str) -> str:
    return PHASE_LABELS.get(scene_name, ("", "#888888"))[1]

def phase_label(scene_name: str) -> str:
    return PHASE_LABELS.get(scene_name, ("", ""))[0]

# ─────────────────────────────────────────────
# 3. SESSION STATE
# ─────────────────────────────────────────────
if "scenes" not in st.session_state:
    st.session_state.scenes = {
        "Scene 1: Initial Staging": {
            "Beat 1: The Setup": [
                {"id": str(uuid.uuid4()), "label": "Internal Doubt",
                 "text": "You feel like you're being lied to.",
                 "mode": "Subtext", "targets": []}
            ]
        }
    }

if "cast"         not in st.session_state: st.session_state.cast         = {}
if "active_scene" not in st.session_state: st.session_state.active_scene = list(st.session_state.scenes.keys())[0]
if "log"          not in st.session_state: st.session_state.log          = []
if "lib_loaded"   not in st.session_state: st.session_state.lib_loaded   = False

# ─────────────────────────────────────────────
# 4. CORE LOGIC  (unchanged from original)
# ─────────────────────────────────────────────
def shuffle_beat(scene_name, beat_name):
    cues        = st.session_state.scenes[scene_name][beat_name]
    actor_names = list(st.session_state.cast.keys())
    if not actor_names:
        st.error("Cannot shuffle: No students in the cast.")
        return
    if not cues:
        st.warning("No cues found in this beat.")
        return
    random.shuffle(actor_names)
    for i, cue in enumerate(cues):
        assigned = [actor_names[i % len(actor_names)]]
        cue["targets"] = assigned
        st.session_state[f"tar_{cue['id']}"] = assigned

def fire_cue_whatsapp(cue):
    if not twilio_client:
        st.error("Twilio Client not initialised. Check your SID and Token.")
        return
    timestamp = time.strftime("%H:%M:%S")
    content   = cue["text"]
    targets   = cue["targets"]
    if not targets:
        st.warning(f"No targets selected for '{cue['label']}'")
        return
    successes = []
    for name in targets:
        phone = st.session_state.cast.get(name)
        if phone:
            try:
                clean = phone.strip()
                if not clean.startswith("+"):
                    clean = "+" + clean
                twilio_client.messages.create(
                    body=content,
                    from_=TWILIO_FROM,
                    to=f"whatsapp:{clean}"
                )
                successes.append(name)
            except Exception as e:
                st.error(f"Error sending to {name}: {e}")
    if successes:
        st.session_state.log.append(
            f"{timestamp} · FIRED '{cue['label']}' → {', '.join(successes)}"
        )
        st.toast(f"✅ Sent to {len(successes)} student(s)")

# ─────────────────────────────────────────────
# 5. DARK EDITORIAL THEME
# ─────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Nexus Command · Here & Now")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,300;0,400;0,500;1,300&family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background-color: #0d0d0d !important;
    color: #f0ede6 !important;
}
.stApp { background-color: #0d0d0d !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] * { color: #b0aba4 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #f0ede6 !important; }

/* ── Inputs ── */
input, textarea, [data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #1a1a1a !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #f0ede6 !important;
    border-radius: 4px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
input:focus, textarea:focus {
    border-color: rgba(200,184,154,0.4) !important;
    outline: none !important;
}

/* ── Buttons ── */
.stButton button {
    background-color: #1a1a1a !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #b0aba4 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.06em !important;
    border-radius: 4px !important;
    transition: all 0.15s !important;
}
.stButton button:hover {
    border-color: rgba(200,184,154,0.4) !important;
    color: #c8b89a !important;
    background-color: #222 !important;
}
/* Primary (fire) button */
.stButton [data-testid="baseButton-primary"] {
    background-color: #1e1a15 !important;
    border-color: rgba(139,115,85,0.5) !important;
    color: #c8b89a !important;
}
.stButton [data-testid="baseButton-primary"]:hover {
    background-color: #2a231a !important;
    border-color: #8b7355 !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background-color: #1a1a1a !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #f0ede6 !important;
}

/* ── Multiselect ── */
[data-testid="stMultiSelect"] > div {
    background-color: #1a1a1a !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}
[data-testid="stMultiSelect"] span {
    background-color: #2a2a2a !important;
    color: #c8b89a !important;
    border: 1px solid rgba(200,184,154,0.25) !important;
}

/* ── Radio ── */
[data-testid="stRadio"] label { color: #888880 !important; font-size: 12px !important; }
[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p { color: #888880 !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: #141414 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 6px !important;
}
[data-testid="stExpander"] summary {
    color: #c8b89a !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.08em !important;
}

/* ── Container / cue card ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #141414 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 6px !important;
    padding: 4px 8px !important;
}

/* ── Titles ── */
h1 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 300 !important;
    font-size: 22px !important;
    letter-spacing: -0.02em !important;
    color: #f0ede6 !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
    padding-bottom: 0.5rem !important;
    margin-bottom: 1.25rem !important;
}
h2 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    font-weight: 500 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #4a4a46 !important;
    margin-bottom: 0.75rem !important;
}
h3 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.08em !important;
    color: #888880 !important;
}

/* ── Caption / log ── */
[data-testid="stCaptionContainer"] p,
.stCaption {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    color: #4a4a46 !important;
}

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

/* ── Toast ── */
[data-testid="stToast"] {
    background-color: #1e1a15 !important;
    border: 1px solid rgba(139,115,85,0.4) !important;
    color: #c8b89a !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 6. PHASE BADGE HELPER
# ─────────────────────────────────────────────
def phase_badge_html(scene_name: str) -> str:
    label  = phase_label(scene_name)
    colour = phase_colour(scene_name)
    if not label:
        return ""
    return (
        f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
        f'letter-spacing:0.1em;text-transform:uppercase;padding:2px 8px;'
        f'border-radius:3px;background:{colour}22;color:{colour};'
        f'border:1px solid {colour}44;margin-left:10px;">{label}</span>'
    )

# ─────────────────────────────────────────────
# 7. SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:

    # ── Wordmark ──
    st.markdown("""
    <div style="padding:0.5rem 0 1.25rem;">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;
                  letter-spacing:0.14em;text-transform:uppercase;
                  color:#4a4a46;margin-bottom:4px;">SSF-2026-HERE-NOW</div>
      <div style="font-family:'IBM Plex Sans',sans-serif;font-size:18px;
                  font-weight:300;letter-spacing:-0.02em;color:#f0ede6;">
        Nexus <span style="color:#c8b89a;font-style:italic;">Command</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Library import ──
    st.markdown("### Library")
    lib_exists = os.path.exists(LIBRARY_PATH)
    if lib_exists:
        if st.button("⬆ Import Cue Library", use_container_width=True):
            st.session_state.scenes     = load_library_into_scenes(LIBRARY_PATH)
            st.session_state.active_scene = list(st.session_state.scenes.keys())[0]
            st.session_state.lib_loaded = True
            st.rerun()
        if st.session_state.lib_loaded:
            st.markdown(
                '<p style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;'
                'color:#5a7d6e;margin-top:4px;">✓ nexus_cue_library.json loaded</p>',
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            '<p style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;'
            'color:#8b3333;">nexus_cue_library.json not found.<br>'
            'Place it alongside ui.py.</p>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── Scene management ──
    st.markdown("### Scenes")
    scene_names = list(st.session_state.scenes.keys())
    st.session_state.active_scene = st.selectbox(
        "Active scene", scene_names,
        index=scene_names.index(st.session_state.active_scene),
        label_visibility="collapsed"
    )
    col_a, col_b = st.columns(2)
    new_scene_name = col_a.text_input("New scene name", label_visibility="collapsed",
                                       placeholder="New scene name…")
    if col_a.button("＋ Scene", use_container_width=True):
        if new_scene_name and new_scene_name not in st.session_state.scenes:
            st.session_state.scenes[new_scene_name] = {"New Beat": []}
            st.session_state.active_scene = new_scene_name
            st.rerun()
    if len(scene_names) > 1:
        if col_b.button("✕ Delete", use_container_width=True):
            del st.session_state.scenes[st.session_state.active_scene]
            st.session_state.active_scene = list(st.session_state.scenes.keys())[0]
            st.rerun()

    st.markdown("---")

    # ── Cast ──
    st.markdown("### Cast")
    c_name  = st.text_input("Student name",   placeholder="Student name…",   label_visibility="collapsed")
    c_phone = st.text_input("WhatsApp number", placeholder="+61400000000",    label_visibility="collapsed")
    if st.button("＋ Add student", use_container_width=True):
        if c_name and c_phone:
            st.session_state.cast[c_name] = c_phone
            st.rerun()

    if st.session_state.cast:
        st.markdown('<div style="margin-top:8px;">', unsafe_allow_html=True)
        for name, num in st.session_state.cast.items():
            st.markdown(
                f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;'
                f'color:#888880;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
                f'<span style="color:#c8b89a;">{name}</span>  {num}</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("✕ Clear cast", use_container_width=True):
            st.session_state.cast = {}
            st.rerun()

    st.markdown("---")

    # ── Cast count ──
    n_cast  = len(st.session_state.cast)
    n_scene = len(st.session_state.scenes)
    n_cues  = sum(
        len(cues)
        for beats in st.session_state.scenes.values()
        for cues  in beats.values()
    )
    st.markdown(
        f'<div style="display:flex;gap:16px;margin-top:4px;">'
        f'<div><div style="font-family:\'IBM Plex Mono\',monospace;font-size:20px;'
        f'font-weight:300;color:#c8b89a;">{n_cast}</div>'
        f'<div style="font-size:9px;letter-spacing:0.1em;text-transform:uppercase;'
        f'color:#4a4a46;">Cast</div></div>'
        f'<div><div style="font-family:\'IBM Plex Mono\',monospace;font-size:20px;'
        f'font-weight:300;color:#c8b89a;">{n_scene}</div>'
        f'<div style="font-size:9px;letter-spacing:0.1em;text-transform:uppercase;'
        f'color:#4a4a46;">Scenes</div></div>'
        f'<div><div style="font-family:\'IBM Plex Mono\',monospace;font-size:20px;'
        f'font-weight:300;color:#c8b89a;">{n_cues}</div>'
        f'<div style="font-size:9px;letter-spacing:0.1em;text-transform:uppercase;'
        f'color:#4a4a46;">Cues</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
# 8. MAIN PANEL
# ─────────────────────────────────────────────
active_scene = st.session_state.active_scene
badge_html   = phase_badge_html(active_scene)

st.markdown(
    f'<h1>{active_scene}{badge_html}</h1>',
    unsafe_allow_html=True
)

active_data = st.session_state.scenes[active_scene]

if st.button("＋ Add Beat", type="secondary"):
    active_data[f"Beat {len(active_data) + 1}"] = []
    st.rerun()

# ── Beat loop ──
for beat_name, cues in list(active_data.items()):
    with st.expander(f"↳  {beat_name}  ·  {len(cues)} cues", expanded=True):

        bc1, bc2, bc3, bc4 = st.columns([2.5, 1, 1, 0.7])

        renamed = bc1.text_input("Rename", beat_name, key=f"r_{beat_name}",
                                  label_visibility="collapsed",
                                  placeholder="Beat name…")
        if renamed != beat_name:
            active_data[renamed] = active_data.pop(beat_name)
            st.rerun()

        if bc2.button("⇄ Shuffle", key=f"s_{beat_name}", use_container_width=True):
            shuffle_beat(active_scene, beat_name)
            st.rerun()

        if bc3.button("▶ Fire all", key=f"fa_{beat_name}", use_container_width=True):
            for c in cues:
                fire_cue_whatsapp(c)

        if bc4.button("✕", key=f"db_{beat_name}", use_container_width=True):
            del active_data[beat_name]
            st.rerun()

        st.markdown('<hr style="margin:0.5rem 0 0.75rem;">', unsafe_allow_html=True)

        # ── Cue cards ──
        for cue in cues:
            with st.container(border=True):

                # Mode colour accent
                mode_colour = "#9e8e7e" if cue["mode"] == "Subtext" else "#7e9e8e"
                mode_bg     = "#9e8e7e22" if cue["mode"] == "Subtext" else "#7e9e8e22"

                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                    f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;'
                    f'font-weight:500;letter-spacing:0.06em;color:#c8b89a;text-transform:uppercase;">'
                    f'{cue["label"]}</span>'
                    f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
                    f'letter-spacing:0.06em;text-transform:uppercase;padding:2px 7px;'
                    f'border-radius:3px;background:{mode_bg};color:{mode_colour};'
                    f'border:1px solid {mode_colour}44;">{cue["mode"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                ch1, ch2, ch3 = st.columns([0.55, 0.35, 0.1])
                cue["label"] = ch1.text_input(
                    "Label", cue["label"], key=f"l_{cue['id']}",
                    label_visibility="collapsed", placeholder="Cue label…"
                )
                cue["mode"] = ch2.radio(
                    "Mode", ["Subtext", "Spoken"],
                    index=0 if cue["mode"] == "Subtext" else 1,
                    key=f"m_{cue['id']}", horizontal=True, label_visibility="collapsed"
                )
                if ch3.button("✕", key=f"d_{cue['id']}"):
                    cues.remove(cue)
                    st.rerun()

                cue["text"] = st.text_area(
                    "Text", cue["text"], height=68,
                    key=f"t_{cue['id']}", label_visibility="collapsed",
                    placeholder="Cue text sent to student's phone…"
                )

                cue["targets"] = st.multiselect(
                    "Recipients",
                    list(st.session_state.cast.keys()),
                    default=[t for t in cue["targets"] if t in st.session_state.cast],
                    key=f"tar_{cue['id']}",
                    placeholder="Select students…"
                )

                if st.button(f"▶  Send — {cue['label']}", key=f"f_{cue['id']}", type="primary"):
                    fire_cue_whatsapp(cue)

        if st.button(f"＋ Add cue to {beat_name}", key=f"ac_{beat_name}"):
            cues.append({
                "id": str(uuid.uuid4()), "label": "New Cue",
                "text": "", "mode": "Subtext", "targets": []
            })
            st.rerun()

# ─────────────────────────────────────────────
# 9. LIVE LOG
# ─────────────────────────────────────────────
st.markdown('<hr style="margin:2rem 0 1rem;">', unsafe_allow_html=True)
st.markdown(
    '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
    'letter-spacing:0.14em;text-transform:uppercase;color:#4a4a46;'
    'margin-bottom:0.75rem;">Live Transmission Log</div>',
    unsafe_allow_html=True
)

if st.session_state.log:
    for entry in reversed(st.session_state.log[-15:]):
        st.markdown(
            f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;'
            f'color:#4a4a46;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
            f'{entry}</div>',
            unsafe_allow_html=True
        )
else:
    st.markdown(
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;'
        'color:#2a2a2a;font-style:italic;">Waiting to fire first cue…</div>',
        unsafe_allow_html=True
    )
