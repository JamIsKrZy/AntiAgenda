import base64
import html
from typing import Any
import streamlit as st

from final_proj_chatbot.models.CharacterRepository import get_character_repo
from final_proj_chatbot.styles.style import inject_styles

st.set_page_config(
    page_title="Power Scaling - Arena",
    layout="wide",
)


# ---------- SVG VS Emblem ----------

def _vs_emblem_svg(size_px: int = 120) -> str:
    """Crisp brushstroke-style VS emblem matching the arena wireframes."""
    return f"""
    <svg width="{size_px}" height="{size_px}" viewBox="0 0 140 140" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="VS">
      <defs>
        <linearGradient id="vsGrad" x1="20" y1="20" x2="120" y2="120" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#D92626"/>
          <stop offset="52%" stop-color="#FF551A"/>
          <stop offset="100%" stop-color="#FFB02E"/>
        </linearGradient>
        <filter id="vsGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.65"/>
        </filter>
      </defs>
      <g filter="url(#vsGlow)">
        <!-- V stroke -->
        <path d="M24 30 L48 92 L78 24 L65 24 L48 67 L36 30 Z" fill="url(#vsGrad)" stroke="#F5F7FA" stroke-width="2.2" stroke-linejoin="round"/>
        <!-- S stroke -->
        <path d="M106 44 C94 36, 74 42, 74 56 C74 71, 108 68, 108 86 C108 102, 82 108, 64 98 L69 88 C82 95, 96 92, 96 85 C96 76, 62 78, 62 56 C62 38, 86 28, 111 36 Z"
              fill="url(#vsGrad)" stroke="#F5F7FA" stroke-width="2.2" stroke-linejoin="round"/>
        <!-- Diagonal slash accent -->
        <path d="M34 112 L114 26 L106 24 L28 109 Z" fill="#FFFFFF" opacity="0.9"/>
      </g>
    </svg>
    """


# ---------- Character & Portrait Helpers ----------

def _get_portrait_src(character: Any) -> str | None:
    """Resolve a portrait URL, data URI, or raw bytes from a Character object."""
    for attr in ("portrait", "image", "image_url", "avatar", "photo"):
        val = getattr(character, attr, None)
        if not val:
            continue
        if isinstance(val, str):
            return val
        if isinstance(val, (bytes, bytearray)):
            encoded = base64.b64encode(val).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    return None


def _get_character_scale(character: Any) -> str | int | float | None:
    """Extract tier/scale/level if present on the Character model."""
    for attr in ("scale", "tier", "power_tier", "level"):
        val = getattr(character, attr, None)
        if val is not None and str(val).strip() != "":
            return val
    return None


def _render_fighter_card(character: Any | None, side_label: str, active: bool = False) -> None:
    """Render the framed 3:4 fighter portrait and compact origin/tier bar."""
    frame_cls = "pw-fighter-frame pw-fighter-frame--active" if active else "pw-fighter-frame"

    if character is None:
        st.html(
            f"""
            <div class="{frame_cls}">
              <div class="pw-portrait pw-portrait--empty">Select {html.escape(side_label)}</div>
            </div>
            """
        )
        return

    src = _get_portrait_src(character)
    name = html.escape(str(getattr(character, "name", side_label)))
    origin = html.escape(str(getattr(character, "origin", "") or "Unknown Origin"))
    scale = _get_character_scale(character)
    scale_badge = f'<span class="pw-fighter-tag">{html.escape(str(scale))}</span>' if scale is not None else ""

    if src:
        portrait_html = f'<img class="pw-portrait" src="{html.escape(src, quote=True)}" alt="{name}" />'
    else:
        portrait_html = f'<div class="pw-portrait pw-portrait--empty">{name}</div>'

    st.html(
        f"""
        <div class="{frame_cls}">
          {portrait_html}
          <div class="pw-fighter-meta">
            <span>{origin}</span>
            {scale_badge}
          </div>
        </div>
        """
    )


# ---------- Narration Engine ----------

def _render_narration_box(lines: list[str]) -> str:
    """Build HTML for the center narration box (old text moves up & dims, new text enlarges in center)."""
    if not lines:
        inner = '<div class="pw-narration-placeholder">Awaiting first clash...</div>'
    else:
        current_line = html.escape(lines[-1])
        history_html = ""

        # Show up to 2 preceding lines pushed upward with decreasing opacity
        previous = lines[:-1][-2:]
        if previous:
            items: list[str] = []
            for idx, old_text in enumerate(previous):
                is_oldest = len(previous) == 2 and idx == 0
                cls = "pw-narration-prev pw-narration-prev--faded" if is_oldest else "pw-narration-prev"
                items.append(f'<div class="{cls}">{html.escape(old_text)}</div>')
            history_html = f'<div class="pw-narration-history">{"".join(items)}</div>'

        inner = f'{history_html}<div class="pw-narration-current">{current_line}</div>'

    return f'<div class="pw-narration-box">{inner}</div>'


def push_narration(text: str) -> None:
    """Append a narration line and immediately update the center stage.

    Safe to call both during a live turn-by-turn loop (via the st.empty slot)
    and across Streamlit reruns (via st.session_state).
    """
    cleaned = text.strip()
    if not cleaned:
        return

    log: list[str] = st.session_state.setdefault("arena_narration_log", [])
    log.append(cleaned)

    slot = st.session_state.get("_arena_narration_slot")
    if slot is not None:
        slot.html(_render_narration_box(log))


def clear_narration() -> None:
    """Reset the narration log for a fresh match."""
    st.session_state["arena_narration_log"] = []
    slot = st.session_state.get("_arena_narration_slot")
    if slot is not None:
        slot.html(_render_narration_box([]))


# ---------- Fight Callback (Plug future battle modules here) ----------

def on_fight_start(fighter_1: Any, fighter_2: Any) -> None:
    """Blanked callback triggered when the user clicks FIGHT.

    Future combat / LLM narration modules will be hooked in here and can
    stream lines directly to the center stage via `push_narration("...")`.
    """
    pass


# ---------- Page State & Layout ----------

def _init_arena_state() -> None:
    st.session_state.setdefault("arena_fighting", False)
    st.session_state.setdefault("arena_narration_log", [])
    st.session_state.setdefault("arena_f1_id", None)
    st.session_state.setdefault("arena_f2_id", None)


def render_arena() -> None:
    _init_arena_state()

    repo = get_character_repo()
    characters = repo.get_all()

    # Resolve selected fighters so we can also tint the arena spotlight to their scale
    char_by_id = {c.id: c for c in characters}
    f1 = char_by_id.get(st.session_state["arena_f1_id"])
    f2 = char_by_id.get(st.session_state["arena_f2_id"])

    active_scale = _get_character_scale(f1) or _get_character_scale(f2)
    inject_styles(scale=active_scale)

    # Handle initial LocalStorage mount or empty roster gracefully
    if not characters:
        st.info("Loading fighters from LocalStorage — or create at least two fighters first to enter the Arena.")
        return

    # Default selection to first two distinct fighters if unset or deleted
    ids = [c.id for c in characters]
    if st.session_state["arena_f1_id"] not in char_by_id:
        st.session_state["arena_f1_id"] = ids[0]
    if st.session_state["arena_f2_id"] not in char_by_id:
        st.session_state["arena_f2_id"] = ids[1] if len(ids) > 1 else ids[0]

    f1 = char_by_id.get(st.session_state["arena_f1_id"])
    f2 = char_by_id.get(st.session_state["arena_f2_id"])
    is_fighting: bool = st.session_state["arena_fighting"]

    # =========================================================================
    # VIEW 1: PRE-FIGHT LOBBY (Wireframe 1)
    # =========================================================================
    if not is_fighting:
        col_left, col_center, col_right = st.columns([1.15, 0.85, 1.15], gap="large")

        with col_left:
            _render_fighter_card(f1, side_label="Fighter 1", active=False)
            st.markdown("<div style='height: 0.6rem'></div>", unsafe_allow_html=True)
            selected_f1 = st.selectbox(
                "Fighter 1",
                options=ids,
                index=ids.index(st.session_state["arena_f1_id"]),
                format_func=lambda cid: char_by_id[cid].name,
                key="arena_select_f1",
                label_visibility="collapsed",
            )
            if selected_f1 != st.session_state["arena_f1_id"]:
                st.session_state["arena_f1_id"] = selected_f1
                st.rerun()

        with col_right:
            _render_fighter_card(f2, side_label="Fighter 2", active=False)
            st.markdown("<div style='height: 0.6rem'></div>", unsafe_allow_html=True)
            selected_f2 = st.selectbox(
                "Fighter 2",
                options=ids,
                index=ids.index(st.session_state["arena_f2_id"]),
                format_func=lambda cid: char_by_id[cid].name,
                key="arena_select_f2",
                label_visibility="collapsed",
            )
            if selected_f2 != st.session_state["arena_f2_id"]:
                st.session_state["arena_f2_id"] = selected_f2
                st.rerun()

        with col_center:
            st.html(f'<div class="pw-vs-wrap pw-vs-wrap--lobby">{_vs_emblem_svg(126)}</div>')

            same_fighter = st.session_state["arena_f1_id"] == st.session_state["arena_f2_id"]
            with st.container(key="fight_btn_wrap"):
                fight_clicked = st.button(
                    "FIGHT",
                    type="primary",
                    use_container_width=True,
                    disabled=same_fighter or len(characters) < 2,
                )

            if len(characters) < 2:
                st.caption("Create at least 2 characters to start a match.")
            elif same_fighter:
                st.caption("Select two different fighters.")

            if fight_clicked and f1 and f2:
                st.session_state["arena_fighting"] = True
                clear_narration()
                on_fight_start(f1, f2)
                st.rerun()

    # =========================================================================
    # VIEW 2: IN-FIGHT NARRATION STAGE (Wireframe 2)
    # =========================================================================
    else:
        col_left, col_center, col_right = st.columns([0.95, 1.5, 0.95], gap="large")

        with col_left:
            _render_fighter_card(f1, side_label="Fighter 1", active=True)
            if f1:
                st.html(f'<div class="pw-fighter-plate">{html.escape(f1.name)}</div>')

        with col_center:
            st.html(f'<div class="pw-vs-wrap pw-vs-wrap--crown">{_vs_emblem_svg(64)}</div>')
            narration_slot = st.empty()
            st.session_state["_arena_narration_slot"] = narration_slot
            narration_slot.html(_render_narration_box(st.session_state["arena_narration_log"]))

            st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
            _, reset_col, _ = st.columns([1, 1.2, 1])
            with reset_col:
                if st.button("Change Fighters", use_container_width=True):
                    st.session_state["arena_fighting"] = False
                    clear_narration()
                    st.rerun()

        with col_right:
            _render_fighter_card(f2, side_label="Fighter 2", active=True)
            if f2:
                st.html(f'<div class="pw-fighter-plate">{html.escape(f2.name)}</div>')


render_arena()