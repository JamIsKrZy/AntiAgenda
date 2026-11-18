"""Small read-only UI pieces shared by the character pages."""

from html import escape

import streamlit as st

from final_proj_chatbot.routes import CHARACTERS, go


def blocks(*parts: str) -> str:
    """Joins HTML blocks with blank lines so markdown leaves their contents alone."""
    return "\n\n".join(parts)


def _text(value: str) -> str:
    """Escapes user text for safe use inside HTML."""
    return escape(value or "").replace("\n", "<br>")


def portrait_html(image: str, name: str = "") -> str:
    if image:
        return (
            f'<div><img class="pw-portrait" src="{escape(image, quote=True)}" '
            f'alt="{escape(name, quote=True)}"></div>'
        )
    return '<div class="pw-portrait pw-portrait--empty">No portrait</div>'


def chips_html(items: list[str]) -> str:
    if not items:
        return '<div class="pw-muted">None yet</div>'
    chips = "".join(f'<span class="pw-chip">{_text(item)}</span>' for item in items)
    return f'<div class="pw-chips">{chips}</div>'


def feats_html(feats: list) -> str:
    if not feats:
        return '<div class="pw-empty">No feats recorded.</div>'
    cards = "".join(f'<div class="pw-feat">{_text(f.description)}</div>' for f in feats)
    return f'<div class="pw-feats">{cards}</div>'


def render_not_found() -> None:
    st.markdown(
        '<div class="pw-empty">We couldn\'t find this character.</div>',
        unsafe_allow_html=True,
    )
    if st.button("Back to characters", icon=":material/arrow_back:"):
        go(CHARACTERS)


@st.dialog("Delete character")
def confirm_delete(character_id: str, name: str) -> None:
    """Asks first. The actual delete runs in the Characters page (see pending_delete)."""
    st.markdown(
        f'<div class="pw-dialog-name">{_text(name)}</div>', unsafe_allow_html=True
    )
    st.write("This character will be removed from this browser. This can't be undone.")
    with st.container(key="confirm_delete"):
        cancel_col, delete_col = st.columns(2)
        if cancel_col.button("Cancel", width="stretch"):
            st.rerun()
        if delete_col.button("Delete", type="primary", width="stretch"):
            st.session_state["pending_delete"] = character_id
            st.rerun()