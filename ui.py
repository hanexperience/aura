import streamlit as st
from twilio.rest import Client
from supabase import create_client, Client as SupabaseClient
import uuid, time, json, os, random
from datetime import date, datetime
from collections import defaultdict
import time

# ─────────────────────────────────────────────
# PAGE CONFIG — must be first Streamlit call
# ─────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Nexus Command · Here & Now")

# ─────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,300;0,400;0,500;1,300&family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background-color: #0d0d0d !important;
    color: #f0ede6 !important;
}
.stApp { background-color: #0d0d0d !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #0d0d0d !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    color: #4a4a46 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.25rem !important;
    border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #c8b89a !important;
    background-color: #141414 !important;
    border-bottom: 1px solid #c8b89a !important;
}

/* Inputs */
input, textarea,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #1a1a1a !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #f0ede6 !important;
    border-radius: 4px !important;
}

/* Buttons */
.stButton button {
    background-color: #1a1a1a !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #b0aba4 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.06em !important;
}
.stButton [data-testid="baseButton-primary"] {
    background-color: #1e1a15 !important;
    border-color: rgba(139,115,85,0.5) !important;
    color: #c8b89a !important;
}

/* Expanders / containers */
[data-testid="stExpander"] {
    background-color: #141414 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #141414 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 6px !important;
}

/* Selectbox */
div[data-testid="stSelectbox"] label {
    color: #4a4a46 !important;
    font-size: 10px !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

/* Headings */
h1 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 300 !important;
    font-size: 22px !important;
    color: #f0ede6 !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
    padding-bottom: 0.5rem !important;
}
h2 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    color: #4a4a46 !important;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CLIENTS
# ─────────────────────────────────────────────
try:
    twilio_client = Client(st.secrets["TWILIO_SID"], st.secrets["TWILIO_TOKEN"])
    TWILIO_FROM = st.secrets["TWILIO_FROM"]
except Exception:
    twilio_client = None
    TWILIO_FROM = ""

try:
    supabase: SupabaseClient = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception:
    supabase = None

LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "nexus_cue_library.json")

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
PHASE_CONFIG = {
    0: ("REHEARSAL ONLY",        "#666666"),
    1: ("PHASE 1 · EXPOSURE",    "#8b7355"),
    2: ("PHASE 2 · FORGETTING",  "#5a7d6e"),
    3: ("PHASE 3 · INTEGRATION", "#6e7a9e"),
}
SCENE_PHASE_MAP = {
    "Scene 1: Arrival":         1,
    "Scene 2: The Reason":      1,
    "Scene 3: The Forgetting":  2,
    "Scene 4: The Integration": 3,
    "Scene 5: Rehearsal Tools": 0,
}

# ─────────────────────────────────────────────
# PUBLIC ONBOARDING VIEW
# ─────────────────────────────────────────────
query_params = st.query_params
if query_params.get("mode") == "join":
    st.markdown("### Join the Nexus Cast")
    
    with st.form("cast_registration"):
        name = st.text_input("Full Name", autocomplete="name")
        phone = st.text_input("WhatsApp Number", placeholder="+61...", autocomplete="tel")
        pronoun = st.selectbox("Pronouns", ["they/them", "she/her", "he/him", "other"])
        
        if st.form_submit_button("Register"):
            if name and phone:
                try:
                    # Save to Supabase and trigger welcome message
                    supabase.table("nexus_cast").insert({
                        "id": str(uuid.uuid4()), "name": name, 
                        "phone": phone, "pronoun": pronoun, "notes": "Self-registered"
                    }).execute()
                    send_whatsapp(phone) 
                    st.success("Welcome to the Nexus. Check your WhatsApp.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please provide name and phone.")
    st.stop() # Stops the dashboard from loading for students

# ─────────────────────────────────────────────
# SUPABASE — CAST
# ─────────────────────────────────────────────
def sb_get_cast():
    if not supabase: return []
    try:
        return supabase.table("nexus_cast").select("*").order("name").execute().data or []
    except: return []

def sb_add_cast(name, phone, pronoun, notes=""):
    """Adds a student to the nexus_cast table with pronouns."""
    if not supabase: return
    supabase.table("nexus_cast").insert({
        "id": str(uuid.uuid4()), 
        "name": name, 
        "phone": phone, 
        "pronoun": pronoun, # Ensure this column exists in Supabase
        "notes": notes
    }).execute()

def sb_delete_cast(cast_id):
    if not supabase: return
    supabase.table("nexus_cast").delete().eq("id", cast_id).execute()

def sb_add_cast(name, phone, pronoun, notes=""):
    if not supabase: return
    supabase.table("nexus_cast").insert({
        "id": str(uuid.uuid4()), "name": name, "phone": phone, 
        "pronoun": pronoun, "notes": notes # Added pronoun here
    }).execute()
    
# ─────────────────────────────────────────────
# SUPABASE — CREW
# ─────────────────────────────────────────────
def sb_get_crew():
    if not supabase: return []
    try:
        return supabase.table("nexus_crew").select("*").order("name").execute().data or []
    except: return []

def sb_add_crew(name, role, phone):
    if not supabase: return
    supabase.table("nexus_crew").insert({
        "id": str(uuid.uuid4()), "name": name, "role": role, "phone": phone
    }).execute()

def sb_delete_crew(crew_id):
    if not supabase: return
    supabase.table("nexus_crew").delete().eq("id", crew_id).execute()

# ─────────────────────────────────────────────
# SUPABASE — CUE LIBRARY
# ─────────────────────────────────────────────
def sb_get_library():
    if not supabase: return []
    try:
        return supabase.table("nexus_cue_library").select("*").order("scene_name").execute().data or []
    except: return []

# From your ui.py
def sb_add_cue(label, text, mode, scene_name, beat_name, phase, rehearsal_day="Performance"):
    """Adds a cue and prevents the 'rehearsal_day' error."""
    if not supabase: return
    supabase.table("nexus_cue_library").insert({
        "id": str(uuid.uuid4()), 
        "label": label, 
        "text": text,
        "mode": mode, 
        "scene_name": scene_name, 
        "beat_name": beat_name, 
        "phase": phase,
        "rehearsal_day": rehearsal_day # Default value added
    }).execute()

def sb_update_cue(cue_id, label, text, mode):
    if not supabase: return
    supabase.table("nexus_cue_library").update({
        "label": label, "text": text, "mode": mode
    }).eq("id", cue_id).execute()

def sb_delete_cue(cue_id):
    if not supabase: return
    supabase.table("nexus_cue_library").delete().eq("id", cue_id).execute()

def seed_library_from_json():
    """One-time import of nexus_cue_library.json → Supabase."""
    if not os.path.exists(LIBRARY_PATH) or not supabase:
        return 0
    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        lib = json.load(f)
    count = 0
    for scene in lib.get("scenes", []):
        scene_name = scene["name"]
        phase = scene.get("phase", 0)
        for beat in scene.get("beats", []):
            beat_name = beat["name"]
            for cue in beat.get("cues", []):
                try:
                    supabase.table("nexus_cue_library").insert({
                        "id":         cue.get("id", str(uuid.uuid4())),
                        "label":      cue["label"],
                        "text":       cue["text"],
                        "mode":       cue.get("mode", "Subtext"),
                        "scene_name": scene_name,
                        "beat_name":  beat_name,
                        "phase":      phase,
                    }).execute()
                    count += 1
                except: pass
    return count

# ─────────────────────────────────────────────
# SUPABASE — SESSIONS
# ─────────────────────────────────────────────
def sb_get_sessions():
    if not supabase: return []
    try:
        return supabase.table("nexus_sessions").select("*").order("session_date", desc=False).execute().data or []
    except: return []

def sb_create_session(name, stype, session_date, notes=""):
    if not supabase: return None
    sid = str(uuid.uuid4())
    supabase.table("nexus_sessions").insert({
        "id": sid, "name": name, "type": stype,
        "session_date": str(session_date), "notes": notes,
        "locked": False, "plan": {}
    }).execute()
    return sid

def sb_update_plan(session_id, plan):
    if not supabase: return
    supabase.table("nexus_sessions").update({"plan": plan}).eq("id", session_id).execute()

def sb_lock_session(session_id):
    if not supabase: return
    supabase.table("nexus_sessions").update({"locked": True}).eq("id", session_id).execute()

def sb_delete_session(session_id):
    if not supabase: return
    supabase.table("nexus_sessions").delete().eq("id", session_id).execute()
    supabase.table("nexus_cue_log").delete().eq("session_id", session_id).execute()

# ─────────────────────────────────────────────
# SUPABASE — LOG
# ─────────────────────────────────────────────
def sb_log_fired(session_id, cue_id, label, text, targets):
    if not supabase: return
    supabase.table("nexus_cue_log").insert({
        "id":         str(uuid.uuid4()),
        "session_id": session_id,
        "cue_id":     cue_id,
        "cue_label":  label,
        "cue_text":   text,
        "targets":    targets,
        "fired_at":   datetime.utcnow().isoformat(),
    }).execute()

def sb_get_log(session_id, limit=25):
    if not supabase: return []
    try:
        return supabase.table("nexus_cue_log").select("*").eq(
            "session_id", session_id
        ).order("fired_at", desc=True).limit(limit).execute().data or []
    except: return []

# ─────────────────────────────────────────────
# TWILIO — FIRE
# ─────────────────────────────────────────────
def send_whatsapp(phone, text=None):
    """Sends a WhatsApp template message via Twilio."""
    if not twilio_client: 
        return False, "Twilio not initialised"
    
    clean = phone.strip()
    if not clean.startswith("+"): 
        clean = "+" + clean
    
    try:
        # Using your specific Aura template and service SIDs
        msg_service_sid = "MG02e2301ca0ca9f7881a0190637323f1d"
        template_sid = "HXe36a26d8401f326ad09ef8b1424d78d9"
        
        twilio_client.messages.create(
            messaging_service_sid=msg_service_sid,
            to=f"whatsapp:{clean}",
            content_sid=template_sid
        )
        return True, ""
    except Exception as e:
        return False, str(e)

def fire_cue(cue_id, label, text, targets, people_lookup, session_id):
    """Fire a cue to a list of target names. Logs successes."""
    if not targets:
        st.warning(f"No recipients selected for '{label}'")
        return
    successes, errors = [], []
    for name in targets:
        phone = people_lookup.get(name)
        if not phone:
            errors.append(f"{name}: no phone")
            continue
        ok, err = send_whatsapp(phone, text)
        if ok:
            successes.append(name)
        else:
            errors.append(f"{name}: {err}")
    if successes:
        sb_log_fired(session_id, cue_id, label, text, successes)
        st.toast(f"✅ '{label}' → {', '.join(successes)}")
    for e in errors:
        st.error(e)

def run_countdown(seconds):
    """Displays a countdown timer in a single updating line."""
    # Create a single placeholder slot
    timer_placeholder = st.empty()
    
    for i in range(seconds, -1, -1):
        # Overwrite the same slot with the new number
        timer_placeholder.markdown(
            f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;'
            f'color:#c8b89a;letter-spacing:0.05em;">⏱ COUNTDOWN: {i}s</div>', 
            unsafe_allow_html=True
        )
        time.sleep(1)
    
    # Clear the timer when done
    timer_placeholder.empty()

def run_nexus_timer(seconds):
    """Counts down in a single, non-scrolling line."""
    # 1. This creates a 'reserved' space in the UI
    timer_slot = st.empty()
    
    for i in range(seconds, -1, -1):
        # 2. This overwrites the SAME space every second
        timer_slot.markdown(
            f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:11px; '
            f'color:#c8b89a; letter-spacing:0.08em; padding: 10px 0;">'
            f'⏱ SYSTEM_COUNTDOWN: {i}s</div>', 
            unsafe_allow_html=True
        )
        time.sleep(1)
    
    # 3. Clean up the slot when finished
    timer_slot.empty()
    
# ─────────────────────────────────────────────
# AUTO-FIRE HELPERS
# ─────────────────────────────────────────────
def _resolve_beat_cues(entries, lib_by_id):
    """Convert plan entries → [(cue_id, base_cue_dict, targets)]. Skips unresolved."""
    result = []
    for entry in entries:
        cue_id = entry.get("cue_id") if isinstance(entry, dict) else entry
        base   = lib_by_id.get(cue_id)
        if base:
            targets = entry.get("targets", []) if isinstance(entry, dict) else []
            result.append((cue_id, base, targets))
    return result

def shuffle_cast_for_beat(entries, cast_names):
    """Assign one cast member per cue, round-robin after shuffling. Modifies entries in-place."""
    if not cast_names or not entries:
        return
    pool = cast_names.copy()
    random.shuffle(pool)
    for i, entry in enumerate(entries):
        if isinstance(entry, dict):
            entry["targets"] = [pool[i % len(pool)]]

def auto_fire_beat_seq(valid_cues, all_people, session_id, wait_sec, beat_name):
    """
    Fires a sequence of cues with a single-line countdown between each.
    Matches the call site: (valid, all_people, session_id, dur_secs, beat_name)
    """
    n = len(valid_cues)
    with st.status(f"Firing {n} cues for '{beat_name}'...", expanded=True) as status:
        # Placeholder to prevent multiple lines
        countdown_slot = st.empty()
        
        for i, (cue_id, base, targets) in enumerate(valid_cues):
            # If not the first cue, wait the specified time
            if i > 0:
                deadline = time.time() + float(wait_sec)
                while time.time() < deadline:
                    remaining = deadline - time.time()
                    # Update the same slot instead of writing a new line
                    countdown_slot.markdown(
                        f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:11px; color:#c8b89a;">'
                        f'Next: <em>{base["label"]}</em> in <strong>{remaining:.0f}s</strong> · [{i + 1}/{n}]</div>',
                        unsafe_allow_html=True
                    )
                    time.sleep(0.4)
                
                # Clear countdown before firing
                countdown_slot.empty()

            # --- FIXED: Using the correct function name 'fire_cue' ---
            fire_cue(cue_id, base["label"], base["text"], targets, all_people, session_id)
            
            tgt_str = ", ".join(targets) if targets else "—"
            status.write(f" ↳ ✅ *{base['label']}* → {tgt_str}")
            
        status.update(label=f"✅ Beat complete · {n} cues sent", state="complete")

def auto_fire_scene(scene_data, all_people, session_id, scene_label):
    """Fire all beats in a scene sequentially with a clean UI."""
    total = sum(len(v) for _, v, _ in scene_data)
    
    with st.status(
        f"🎬  {scene_label}  ·  {total} cues across {len(scene_data)} beats",
        expanded=True
    ) as status:
        countdown_slot = st.empty()
        
        for beat_name, valid_cues, duration_secs in scene_data:
            n = len(valid_cues)
            dur_label = f"{duration_secs / 60:.1f} min" if duration_secs > 0 else "instant"
            status.write(f"**{beat_name}** · {n} cues · {dur_label}")
            
            if duration_secs <= 0:
                offsets = [i * 0.35 for i in range(n)]
            else:
                offsets = sorted(random.uniform(0, duration_secs) for _ in range(n))
            
            beat_start = time.time()
            for i, ((cue_id, base, targets), offset) in enumerate(zip(valid_cues, offsets)):
                elapsed = time.time() - beat_start
                wait = offset - elapsed
                
                if wait > 0:
                    deadline = time.time() + wait
                    while time.time() < deadline:
                        remaining = deadline - time.time()
                        countdown_slot.markdown(
                            f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:11px; color:#c8b89a; margin-left: 20px;">'
                            f'↳ Next: <em>{base["label"]}</em> in <strong>{remaining:.0f}s</strong> [{i + 1}/{n}]</div>',
                            unsafe_allow_html=True
                        )
                        time.sleep(0.4)
                    countdown_slot.empty()

                # --- FIXED: Using the correct function name 'fire_cue' ---
                fire_cue(cue_id, base["label"], base["text"], targets, all_people, session_id)
                tgt_str = ", ".join(targets) if targets else "—"
                status.write(f"  ↳ ✅ *{base['label']}* → {tgt_str}")
                
        status.update(label=f"✅ Scene complete · {total} cues sent", state="complete")
        
# ─────────────────────────────────────────────
# HTML HELPERS
# ─────────────────────────────────────────────
def mono(text, size="11px", color="#b0aba4"):
    return (
        f'<span style="font-family:\'IBM Plex Mono\',monospace;'
        f'font-size:{size};color:{color};">{text}</span>'
    )

def phase_badge(phase: int) -> str:
    label, colour = PHASE_CONFIG.get(phase, ("", "#888888"))
    if not label: return ""
    return (
        f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
        f'letter-spacing:0.1em;text-transform:uppercase;padding:2px 8px;'
        f'border-radius:3px;background:{colour}22;color:{colour};'
        f'border:1px solid {colour}44;">{label}</span>'
    )

def mode_badge(mode: str) -> str:
    colours = {"Subtext": "#9e8e7e", "Spoken": "#7e9e8e", "Targeted": "#8e7e9e"}
    c = colours.get(mode, "#888888")
    return (
        f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
        f'padding:2px 7px;border-radius:3px;background:{c}22;color:{c};'
        f'border:1px solid {c}44;">{mode}</span>'
    )

def divider():
    st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:1rem 0;">', unsafe_allow_html=True)

def section_label(text, color="#4a4a46"):
    st.markdown(
        f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
        f'letter-spacing:0.14em;text-transform:uppercase;color:{color};'
        f'margin-bottom:0.6rem;">{text}</div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="padding:0.75rem 0 0.5rem;">
  <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:0.14em;
       text-transform:uppercase;color:#4a4a46;margin-bottom:4px;">SSF-2026-HERE-NOW</div>
  <div style="font-family:'IBM Plex Sans',sans-serif;font-size:24px;font-weight:300;
       letter-spacing:-0.02em;color:#f0ede6;">
    Nexus <span style="color:#c8b89a;font-style:italic;">Command</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_fire, tab_sessions, tab_library, tab_people = st.tabs([
    "🎬  Fire",
    "📋  Sessions",
    "📚  Library",
    "👥  People",
])

# ═══════════════════════════════════════════════════════════════
# TAB 1 · FIRE
# ═══════════════════════════════════════════════════════════════
with tab_fire:
    sessions_all = sb_get_sessions()
    cast_list    = sb_get_cast()
    crew_list    = sb_get_crew()
    cast_lookup  = {p["name"]: p["phone"] for p in cast_list}
    crew_lookup  = {p["name"]: p["phone"] for p in crew_list}
    all_people   = {**cast_lookup, **crew_lookup}
    all_names    = list(cast_lookup.keys()) + list(crew_lookup.keys())

    if not sessions_all:
        st.info("No sessions yet — create one in the Sessions tab.")
    else:
        # Session selector
        rehearsals   = [s for s in sessions_all if s["type"] == "rehearsal"]
        performances = [s for s in sessions_all if s["type"] == "performance"]

        def session_label(s):
            lock = "🔒 " if s.get("locked") else ""
            return f"{lock}{s['name']}  ·  {s['session_date']}"

        fire_col1, fire_col2 = st.columns([4, 1])
        with fire_col1:
            all_for_select = sessions_all
            labels = [session_label(s) for s in all_for_select]
            chosen_idx = fire_col1.selectbox(
                "Session", range(len(labels)),
                format_func=lambda i: labels[i],
                key="fire_session_select",
                label_visibility="collapsed"
            )
        active = all_for_select[chosen_idx]
        locked = active.get("locked", False)
        stype  = active.get("type", "rehearsal")
        colour = "#8b7355" if stype == "performance" else "#5a7d6e"

        fire_col2.markdown(
            f'<div style="padding:6px 10px;border-radius:4px;'
            f'background:{colour}11;border:1px solid {colour}33;'
            f'font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
            f'letter-spacing:0.08em;color:{colour};text-transform:uppercase;'
            f'text-align:center;">{"🔒 LOCKED" if locked else stype}</div>',
            unsafe_allow_html=True
        )

        session_id = active["id"]
        plan = active.get("plan") or {}
        library = sb_get_library()
        lib_by_id = {c["id"]: c for c in library}

        if not plan:
            st.markdown(
                f'{mono("No cues planned for this session. Build the plan in the Sessions tab.", "12px", "#4a4a46")}',
                unsafe_allow_html=True
            )
        else:
            cast_names_only = list(cast_lookup.keys())

            for scene_name, beats in plan.items():
                phase = SCENE_PHASE_MAP.get(scene_name, 0)
                _, pc = PHASE_CONFIG.get(phase, ("", "#888888"))

                # Scene header + Fire Scene button
                sh1, sh2 = st.columns([4, 1])
                sh1.markdown(
                    f'<div style="margin-top:1.5rem;margin-bottom:0.4rem;'
                    f'font-family:\'IBM Plex Mono\',monospace;font-size:10px;'
                    f'letter-spacing:0.1em;text-transform:uppercase;color:{pc};">'
                    f'{scene_name} &nbsp;{phase_badge(phase)}</div>',
                    unsafe_allow_html=True
                )
                if sh2.button(
                    "\U0001f3ac Fire Scene",
                    key=f"fire_scene_{session_id}_{scene_name}",
                    use_container_width=True
                ):
                    if locked:
                        st.warning("Session is locked.")
                    else:
                        scene_data = []
                        for bn, ents in beats.items():
                            dur_secs = st.session_state.get(
                                f"dur_{session_id}_{bn}", 2.0
                            ) * 60
                            valid = _resolve_beat_cues(ents, lib_by_id)
                            if valid:
                                scene_data.append((bn, valid, dur_secs))
                        if scene_data:
                            auto_fire_scene(scene_data, all_people, session_id, scene_name)
                            sb_update_plan(session_id, plan)

                # Beat loops
                for beat_name, entries in beats.items():
                    valid_count = sum(
                        1 for e in entries
                        if lib_by_id.get(e.get("cue_id") if isinstance(e, dict) else e)
                    )
                    with st.expander(f"\u21b3 {beat_name}  \u00b7  {valid_count} cues", expanded=True):

                        # Beat control bar
                        dur_key = f"dur_{session_id}_{beat_name}"
                        if dur_key not in st.session_state:
                            st.session_state[dur_key] = 2.0

                        bc1, bc2, bc3, bc4 = st.columns([1.8, 1, 1, 1])
                        bc1.markdown(mono("Duration (min)", "9px", "#4a4a46"), unsafe_allow_html=True)
                        new_dur = bc1.number_input(
                            "min", min_value=0.0, max_value=30.0, step=0.5,
                            value=float(st.session_state[dur_key]),
                            key=f"dur_input_{session_id}_{beat_name}",
                            label_visibility="collapsed", format="%.1f"
                        )
                        st.session_state[dur_key] = new_dur

                        if bc2.button(
                            "\u21c4 Shuffle",
                            key=f"shuf_{session_id}_{beat_name}",
                            use_container_width=True
                        ):
                            if not locked and cast_names_only:
                                shuffle_cast_for_beat(entries, cast_names_only)
                                sb_update_plan(session_id, plan)
                                st.rerun()

                        if bc3.button(
                            "\u25b6 All",
                            key=f"fall_{session_id}_{beat_name}",
                            use_container_width=True,
                            help="Fire all cues instantly with small stagger"
                        ):
                            if locked:
                                st.warning("Session is locked.")
                            else:
                                valid = _resolve_beat_cues(entries, lib_by_id)
                                auto_fire_beat_seq(valid, all_people, session_id, 0, beat_name)
                                sb_update_plan(session_id, plan)

                        if bc4.button(
                            "\u23f1 Auto",
                            key=f"auto_{session_id}_{beat_name}",
                            use_container_width=True,
                            type="primary",
                            help="Randomise cues across the set duration window"
                        ):
                            if locked:
                                st.warning("Session is locked.")
                            else:
                                valid    = _resolve_beat_cues(entries, lib_by_id)
                                dur_secs = st.session_state[dur_key] * 60
                                auto_fire_beat_seq(
                                    valid, all_people, session_id, dur_secs, beat_name
                                )
                                sb_update_plan(session_id, plan)

                        st.markdown(
                            '<hr style="border-color:rgba(255,255,255,0.05);margin:0.5rem 0;">',
                            unsafe_allow_html=True
                        )

                        # Individual cues
                        for entry in entries:
                            cue_id = entry.get("cue_id") if isinstance(entry, dict) else entry
                            base   = lib_by_id.get(cue_id)
                            if not base:
                                continue
                            stored_targets = entry.get("targets", []) if isinstance(entry, dict) else []
                            with st.container(border=True):
                                h1, h2 = st.columns([5, 1])
                                h1.markdown(
                                    f'{mono(base["label"], "12px", "#c8b89a")} &nbsp;{mode_badge(base["mode"])}',
                                    unsafe_allow_html=True
                                )
                                h1.markdown(
                                    f'<div style="font-size:13px;color:#d0cdc6;padding:4px 0 8px;'
                                    f'line-height:1.55;">{base["text"]}</div>',
                                    unsafe_allow_html=True
                                )
                                tar_key  = f"ft_{session_id}_{cue_id}"
                                selected = h1.multiselect(
                                    "Recipients", all_names,
                                    default=[t for t in stored_targets if t in all_names],
                                    key=tar_key, label_visibility="collapsed"
                                )
                                if isinstance(entry, dict):
                                    entry["targets"] = selected
                                if h2.button(
                                    "\u25b6", key=f"fire_{session_id}_{cue_id}",
                                    type="primary", use_container_width=True
                                ):
                                    if locked:
                                        st.warning("Session is locked.")
                                    else:
                                        fire_cue(
                                            cue_id, base["label"], base["text"],
                                            selected, all_people, session_id
                                        )
                                        sb_update_plan(session_id, plan)

        # Live log
        divider()
        section_label("Live Transmission Log")
        log_entries = sb_get_log(session_id)
        if log_entries:
            for e in log_entries:
                ts  = (e.get("fired_at") or "")[:19].replace("T", " ")
                tgt = ", ".join(e.get("targets") or [])
                st.markdown(
                    f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;'
                    f'color:#4a4a46;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
                    f'{ts} · FIRED <span style="color:#888880;">\'{e["cue_label"]}\' </span>'
                    f' → {tgt}</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                mono("Waiting to fire first cue\u2026", "11px", "#2a2a2a"),
                unsafe_allow_html=True
            )


# ═══════════════════════════════════════════════════════════════
# TAB 2 · SESSIONS
# ═══════════════════════════════════════════════════════════════
with tab_sessions:
    sessions_all = sb_get_sessions()
    library      = sb_get_library()
    lib_by_id    = {c["id"]: c for c in library}

    left, right = st.columns([1, 2])

    with left:
        section_label("Sessions")

        with st.expander("＋ New Session", expanded=not sessions_all):
            ns_name  = st.text_input("Session name", placeholder="Mon 4 May — Actor Workshop", key="ns_name")
            ns_type  = st.radio("Type", ["rehearsal", "performance"], horizontal=True, key="ns_type")
            ns_date  = st.date_input("Date", value=date(2026, 5, 4), key="ns_date")
            ns_notes = st.text_area("Notes", height=56, placeholder="Brief intent…", key="ns_notes")
            if st.button("＋ Add Student", use_container_width=True, key="add_cast"):
                if add_c_name and add_c_phone:
                    # Now passing 4 arguments: name, phone, pronoun, notes
                    sb_add_cast(add_c_name, add_c_phone, add_c_pronoun, add_c_notes)
                    st.rerun()

        rehearsals   = [s for s in sessions_all if s["type"] == "rehearsal"]
        performances = [s for s in sessions_all if s["type"] == "performance"]

        if rehearsals:
            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
            section_label("Rehearsals", "#666666")
            for s in rehearsals:
                is_active = st.session_state.get("sess_edit") == s["id"]
                icon = "🔒 " if s.get("locked") else ""
                if st.button(f"{icon}{s['name']}", key=f"sb_{s['id']}",
                             use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state["sess_edit"] = s["id"]
                    st.rerun()

        if performances:
            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
            section_label("Performance", "#8b7355")
            for s in performances:
                is_active = st.session_state.get("sess_edit") == s["id"]
                icon = "🔒 " if s.get("locked") else ""
                if st.button(f"{icon}{s['name']}", key=f"sb_{s['id']}",
                             use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state["sess_edit"] = s["id"]
                    st.rerun()

    with right:
        edit_id = st.session_state.get("sess_edit")
        editing = next((s for s in sessions_all if s["id"] == edit_id), None)

        if not editing:
            st.markdown(
                '<div style="color:#2a2a2a;font-family:\'IBM Plex Mono\',monospace;'
                'font-size:12px;padding:2rem 0;">← Select a session to build its plan</div>',
                unsafe_allow_html=True
            )
        else:
            plan   = editing.get("plan") or {}
            locked = editing.get("locked", False)

            hc1, hc2, hc3 = st.columns([4, 1, 1])
            hc1.markdown(
                f'<div style="font-family:\'IBM Plex Sans\',sans-serif;font-size:18px;'
                f'font-weight:300;color:#f0ede6;">{editing["name"]}</div>'
                f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
                f'color:#4a4a46;text-transform:uppercase;">'
                f'{editing["type"]} · {editing["session_date"]}</div>',
                unsafe_allow_html=True
            )
            if not locked:
                if hc2.button("🔒 Lock", use_container_width=True, key=f"lock_{edit_id}"):
                    sb_lock_session(edit_id)
                    st.rerun()
                if hc3.button("🗑 Delete", use_container_width=True, key=f"del_{edit_id}"):
                    sb_delete_session(edit_id)
                    del st.session_state["sess_edit"]
                    st.rerun()
            else:
                hc2.markdown(
                    '<div style="padding:6px;background:#1e1515;border:1px solid rgba(180,60,60,0.3);'
                    'border-radius:4px;font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
                    'color:#c87070;text-align:center;">🔒 LOCKED</div>',
                    unsafe_allow_html=True
                )

            divider()

            if locked:
                section_label("Plan — read only")
                for scene_name, beats in plan.items():
                    phase = SCENE_PHASE_MAP.get(scene_name, 0)
                    st.markdown(f'**{scene_name}** &nbsp;{phase_badge(phase)}', unsafe_allow_html=True)
                    for beat_name, entries in beats.items():
                        labels = [
                            lib_by_id.get(
                                e.get("cue_id") if isinstance(e, dict) else e, {}
                            ).get("label", "?")
                            for e in entries
                        ]
                        st.markdown(
                            f'{mono(f"↳ {beat_name}", "11px", "#888880")} &nbsp;'
                            f'{mono(", ".join(labels), "10px", "#4a4a46")}',
                            unsafe_allow_html=True
                        )
            else:
                section_label("Plan Builder")

                all_scene_names = sorted(set(c["scene_name"] for c in library))
                addable_scenes  = [s for s in all_scene_names if s not in plan] + ["Custom…"]
                with st.expander("＋ Add Scene to Plan"):
                    sc_choice = st.selectbox("Scene", addable_scenes,
                                             key=f"sc_{edit_id}", label_visibility="collapsed")
                    sc_custom = ""
                    if sc_choice == "Custom…":
                        sc_custom = st.text_input("Scene name", key=f"sc_custom_{edit_id}")
                    if st.button("Add Scene", key=f"add_sc_{edit_id}", type="primary"):
                        name = sc_custom if sc_choice == "Custom…" else sc_choice
                        if name and name not in plan:
                            plan[name] = {}
                            sb_update_plan(edit_id, plan)
                            st.rerun()

                for scene_name in list(plan.keys()):
                    beats = plan[scene_name]
                    phase = SCENE_PHASE_MAP.get(scene_name, 0)
                    _, pc = PHASE_CONFIG.get(phase, ("", "#888888"))

                    with st.expander(
                        f"{scene_name}  ·  {sum(len(v) for v in beats.values())} cues",
                        expanded=True
                    ):
                        row1, row2 = st.columns([5, 1])
                        row1.markdown(phase_badge(phase), unsafe_allow_html=True)
                        if row2.button("Remove", key=f"rm_sc_{edit_id}_{scene_name}"):
                            del plan[scene_name]
                            sb_update_plan(edit_id, plan)
                            st.rerun()

                        lib_beats   = sorted(set(
                            c["beat_name"] for c in library if c["scene_name"] == scene_name
                        ))
                        avail_beats = [b for b in lib_beats if b not in beats] + ["Custom…"]
                        ba1, ba2    = st.columns([4, 1])
                        beat_pick   = ba1.selectbox("Beat", avail_beats,
                                                    key=f"bp_{edit_id}_{scene_name}",
                                                    label_visibility="collapsed")
                        bc_custom = ""
                        if beat_pick == "Custom…":
                            bc_custom = ba1.text_input("Beat name", key=f"bc_{edit_id}_{scene_name}")
                        if ba2.button("＋ Beat", key=f"add_bt_{edit_id}_{scene_name}",
                                     use_container_width=True):
                            bname = bc_custom if beat_pick == "Custom…" else beat_pick
                            if bname and bname not in beats:
                                beats[bname] = []
                                sb_update_plan(edit_id, plan)
                                st.rerun()

                        for beat_name in list(beats.keys()):
                            entries = beats[beat_name]
                            st.markdown(
                                f'<div style="font-family:\'IBM Plex Mono\',monospace;'
                                f'font-size:10px;color:#888880;margin:0.75rem 0 0.25rem;'
                                f'border-top:1px solid rgba(255,255,255,0.05);padding-top:0.5rem;">'
                                f'↳ {beat_name}</div>',
                                unsafe_allow_html=True
                            )
                            for entry in list(entries):
                                cue_id = entry.get("cue_id") if isinstance(entry, dict) else entry
                                base   = lib_by_id.get(cue_id, {})
                                if base:
                                    ce1, ce2 = st.columns([6, 1])
                                    ce1.markdown(
                                        f'{mono(base["label"], "11px", "#c8b89a")} &nbsp;{mode_badge(base["mode"])}',
                                        unsafe_allow_html=True
                                    )
                                    if ce2.button("✕", key=f"rm_cue_{edit_id}_{beat_name}_{cue_id}"):
                                        entries.remove(entry)
                                        sb_update_plan(edit_id, plan)
                                        st.rerun()

                            existing_ids = [
                                e.get("cue_id") if isinstance(e, dict) else e for e in entries
                            ]
                            addable_cues = [
                                c for c in library
                                if c["scene_name"] == scene_name
                                and c["beat_name"] == beat_name
                                and c["id"] not in existing_ids
                            ]
                            if addable_cues:
                                opts = {f"{c['label']} ({c['mode']})": c["id"] for c in addable_cues}
                                aca, acb = st.columns([5, 1])
                                chosen_lbl = aca.selectbox(
                                    "Add cue", list(opts.keys()),
                                    key=f"cue_pick_{edit_id}_{beat_name}",
                                    label_visibility="collapsed"
                                )
                                if acb.button("＋", key=f"add_cue_{edit_id}_{beat_name}"):
                                    entries.append({"cue_id": opts[chosen_lbl], "targets": []})
                                    sb_update_plan(edit_id, plan)
                                    st.rerun()

                            if st.button(f"✕ Remove beat", key=f"rm_bt_{edit_id}_{beat_name}"):
                                del beats[beat_name]
                                sb_update_plan(edit_id, plan)
                                st.rerun()


# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# TAB 3 · LIBRARY
# ═══════════════════════════════════════════════════════════════
with tab_library:
    library = sb_get_library()

    lh1, lh2 = st.columns([4, 1])
    lh1.markdown(
        f'<div style="font-family:\'IBM Plex Sans\',sans-serif;font-size:18px;'
        f'font-weight:300;color:#f0ede6;">Cue Library &nbsp;'
        f'{mono(str(len(library)) + " cues", "12px", "#4a4a46")}</div>',
        unsafe_allow_html=True
    )
    if not library:
        if lh2.button("⬆ Seed from JSON", use_container_width=True, key="seed_btn"):
            n = seed_library_from_json()
            st.success(f"Imported {n} cues")
            st.rerun()

    divider()
    fc1, fc2, fc3 = st.columns(3)
    phase_opts = ["All Phases"] + [PHASE_CONFIG[p][0] for p in [1, 2, 3, 0]]
    mode_opts  = ["All Modes", "Subtext", "Spoken", "Targeted"]
    scene_opts = ["All Scenes"] + sorted(set(c["scene_name"] for c in library))

    f_phase = fc1.selectbox("Phase", phase_opts, key="lib_f_phase", label_visibility="collapsed")
    f_mode  = fc2.selectbox("Mode",  mode_opts,  key="lib_f_mode",  label_visibility="collapsed")
    f_scene = fc3.selectbox("Scene", scene_opts, key="lib_f_scene", label_visibility="collapsed")

    filtered = library
    if f_phase != "All Phases":
        target_phase = next(k for k, v in PHASE_CONFIG.items() if v[0] == f_phase)
        filtered = [c for c in filtered if c.get("phase") == target_phase]
    if f_mode != "All Modes":
        filtered = [c for c in filtered if c.get("mode") == f_mode]
    if f_scene != "All Scenes":
        filtered = [c for c in filtered if c.get("scene_name") == f_scene]

    grouped = defaultdict(lambda: defaultdict(list))
    for cue in filtered:
        grouped[cue["scene_name"]][cue["beat_name"]].append(cue)

    for scene_name, beats in grouped.items():
        phase = SCENE_PHASE_MAP.get(scene_name, 0)
        _, pc = PHASE_CONFIG.get(phase, ("", "#888888"))
        st.markdown(
            f'<div style="margin-top:1.5rem;margin-bottom:0.5rem;'
            f'font-family:\'IBM Plex Mono\',monospace;font-size:10px;'
            f'letter-spacing:0.1em;text-transform:uppercase;color:{pc};">'
            f'{scene_name} &nbsp;{phase_badge(phase)}</div>',
            unsafe_allow_html=True
        )
        for beat_name, cues in beats.items():
            with st.expander(f"↳ {beat_name}  ·  {len(cues)} cues"):
                for cue in cues:
                    with st.container(border=True):
                        cc1, cc2 = st.columns([6, 1])
                        cc1.markdown(
                            f'{mono(cue["label"], "11px", "#c8b89a")} &nbsp;{mode_badge(cue["mode"])}',
                            unsafe_allow_html=True
                        )
                        cc1.markdown(
                            f'<div style="font-size:13px;color:#d0cdc6;padding:4px 0;line-height:1.55;">'
                            f'{cue["text"]}</div>',
                            unsafe_allow_html=True
                        )
                        with cc2:
                            if st.button("✎", key=f"ed_{cue['id']}"):
                                current = st.session_state.get(f"editing_{cue['id']}", False)
                                st.session_state[f"editing_{cue['id']}"] = not current
                            if st.button("✕", key=f"dl_{cue['id']}"):
                                sb_delete_cue(cue["id"])
                                st.rerun()
                        if st.session_state.get(f"editing_{cue['id']}"):
                            e_label = st.text_input("Label", cue["label"], key=f"el_{cue['id']}")
                            e_text  = st.text_area("Text", cue["text"], key=f"et_{cue['id']}", height=80)
                            e_mode  = st.radio(
                                "Mode", ["Subtext", "Spoken", "Targeted"],
                                index=["Subtext","Spoken","Targeted"].index(cue.get("mode","Subtext")),
                                key=f"em_{cue['id']}", horizontal=True
                            )
                            if st.button("Save", key=f"sv_{cue['id']}", type="primary"):
                                sb_update_cue(cue["id"], e_label, e_text, e_mode)
                                st.session_state.pop(f"editing_{cue['id']}", None)
                                st.rerun()

    divider()
    section_label("Add New Cue to Library")

    nc1, nc2 = st.columns(2)
    new_label = nc1.text_input("Label", placeholder="Cue label…", key="ncl")
    new_mode  = nc2.radio("Mode", ["Subtext", "Spoken", "Targeted"], key="ncm", horizontal=True)
    new_text  = st.text_area("Text", placeholder="The message sent to the student…", key="nct", height=80)

    scene_choices = sorted(set(c["scene_name"] for c in library)) + ["New Scene…"]
    nc3, nc4 = st.columns(2)
    new_scene = nc3.selectbox("Scene", scene_choices, key="ncs", label_visibility="collapsed")
    if new_scene == "New Scene…":
        new_scene = nc3.text_input("Scene name", key="ncs_custom")

    beat_choices = sorted(set(
        c["beat_name"] for c in library if c["scene_name"] == new_scene
    )) + ["New Beat…"]
    new_beat = nc4.selectbox("Beat", beat_choices, key="ncb", label_visibility="collapsed")
    if new_beat == "New Beat…":
        new_beat = nc4.text_input("Beat name", key="ncb_custom")

    new_phase = SCENE_PHASE_MAP.get(new_scene, 0)

    if st.button("＋ Add to Library", type="primary", key="add_to_lib"):
        if new_label and new_text and new_scene and new_beat:
            sb_add_cue(new_label, new_text, new_mode, new_scene, new_beat, new_phase)
            st.toast(f"✅ '{new_label}' added to library")
            st.rerun()

# ═══════════════════════════════════════════════════════════════
# TAB 4 · PEOPLE
# ═══════════════════════════════════════════════════════════════
with tab_people:
    # --- QR SECTION ---
    with st.expander("📢 ENROLLMENT QR CODE"):
        reg_url = "https://your-app-url.streamlit.app/?mode=join"
        st.write("Display this for student enrollment:")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={reg_url}")
        st.code(reg_url)
    
    cast_list = sb_get_cast()
    crew_list = sb_get_crew() # Ensure crew_list is fetched for pc2

    pc1, pc2 = st.columns(2)

    with pc1:
        section_label(f"Cast · {len(cast_list)} Students", "#8b7355")
        for p in cast_list:
            # Updated to 4 columns to fit Pronouns
            r1, r2, r3, r4 = st.columns([2.5, 1.5, 2, 0.5]) 
            r1.markdown(mono(p["name"], "12px", "#c8b89a"), unsafe_allow_html=True)
            # Displaying the Pronoun
            r2.markdown(mono(p.get("pronoun", ""), "10px", "#666666"), unsafe_allow_html=True) 
            r3.markdown(mono(p["phone"], "10px", "#4a4a46"), unsafe_allow_html=True)
            if r4.button("✕", key=f"dc_{p['id']}"):
                sb_delete_cast(p["id"])
                st.rerun()
            if p.get("notes"):
                st.markdown(mono(p["notes"], "10px", "#3a3a36"), unsafe_allow_html=True)

        divider()
        # manual Add Student form with Pronoun selector
        ca, cb, cc = st.columns([3, 2, 3])
        add_c_name = ca.text_input("Name", placeholder="Name…", key="ac_name", label_visibility="collapsed")
        add_c_pronoun = cb.selectbox("Pronoun", ["they/them", "she/her", "he/him", "other"], key="ac_pronoun", label_visibility="collapsed")
        add_c_phone = cc.text_input("Phone", placeholder="+61...", key="ac_phone", label_visibility="collapsed")
        
        add_c_notes = st.text_input("Notes (optional)",
                                    placeholder="e.g. Year 11",
                                    key="ac_notes", label_visibility="collapsed")
        
        if st.button("＋ Add Student", use_container_width=True, key="add_cast"):
            if add_c_name and add_c_phone:
                # Passing pronouns to the database function
                sb_add_cast(add_c_name, add_c_phone, add_c_pronoun, add_c_notes)
                st.rerun()

    with pc2:
        section_label(f"Crew · {len(crew_list)} Members", "#5a7d6e")
        for p in crew_list:
            r1, r2, r3, r4 = st.columns([2.5, 2, 2, 0.5])
            r1.markdown(mono(p["name"], "12px", "#d0cdc6"), unsafe_allow_html=True)
            r2.markdown(mono(p.get("role", ""), "10px", "#5a7d6e"), unsafe_allow_html=True)
            r3.markdown(mono(p["phone"], "10px", "#4a4a46"), unsafe_allow_html=True)
            if r4.button("✕", key=f"dcr_{p['id']}"):
                sb_delete_crew(p["id"])
                st.rerun()

        divider()
        cra, crb = st.columns(2)
        add_cr_name  = cra.text_input("Name", placeholder="Crew name…",    key="acr_name",  label_visibility="collapsed")
        add_cr_role  = crb.text_input("Role", placeholder="e.g. Camera 1", key="acr_role",  label_visibility="collapsed")
        add_cr_phone = st.text_input("Phone", placeholder="+61400000000",   key="acr_phone", label_visibility="collapsed")
        if st.button("＋ Add Crew Member", use_container_width=True, key="add_crew"):
            if add_cr_name and add_cr_phone:
                sb_add_crew(add_cr_name, add_cr_role, add_cr_phone)
                st.rerun()

    divider()
    section_label("WhatsApp Handshake Test")
    all_people_list = cast_list + crew_list
    all_names_test  = [p["name"] for p in all_people_list]
    all_phones_test = {p["name"]: p["phone"] for p in all_people_list}

    tw1, tw2 = st.columns(2)
    test_who = tw1.selectbox("Recipient", ["—"] + all_names_test,
                             key="tw_who", label_visibility="collapsed")
    test_msg = tw2.text_input("Message", placeholder="Test message…",
                              key="tw_msg", label_visibility="collapsed")
    if st.button("Send Test", key="tw_send"):
        if test_who != "—" and test_msg:
            ok, err = send_whatsapp(all_phones_test.get(test_who, ""), test_msg)
            if ok:
                st.success(f"✅ Sent to {test_who}")
            else:
                st.error(f"Failed: {err}")