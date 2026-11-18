from html import escape

import streamlit as st

from final_proj_chatbot.pages.templates.character_ui import blocks, chips_html, confirm_delete, feats_html, portrait_html, render_not_found
from final_proj_chatbot.models.CharacterRepository import get_character_repo
from final_proj_chatbot.routes import CHARACTERS, EDIT, go, selected_character_id
from final_proj_chatbot.styles.style import inject_styles

st.set_page_config(
    page_title="Power Scaling - Character Details ❤️‍🔥❤️‍🔥❤️‍🔥",
    layout="wide",
)
inject_styles()

repo = get_character_repo()

# A delete was confirmed here: the Characters page carries it out.
if st.session_state.get("pending_delete"):
    go(CHARACTERS)

character = repo.get_character(selected_character_id())
if character is None:
    render_not_found()
    st.stop()

if st.button("Characters", icon=":material/arrow_back:", type="tertiary"):
    go(CHARACTERS)

left, right = st.columns([1, 2], gap="large")

with left:
    with st.container(key="profile_card"):
        st.markdown(
            blocks(
                portrait_html(character.image, character.name),
                f'<div class="pw-name">{escape(character.name)}</div>',
                f'<div class="pw-origin">{escape(character.origin)}</div>',
                '<div class="pw-label">Power ups</div>',
                chips_html(character.power_ups),
            ),
            unsafe_allow_html=True,
        )
        delete_col, edit_col = st.columns(2)
        if delete_col.button("Delete", icon=":material/delete:", key="del_current", width="stretch"):
            confirm_delete(character.id, character.name)
        if edit_col.button("Edit", icon=":material/edit:", type="primary", width="stretch"):
            go(EDIT, character.id)

with right:
    with st.container(key="feats_card"):
        st.markdown('<div class="pw-title">Feats</div>', unsafe_allow_html=True)
        with st.container(height=380, border=False, key="feats_scroll"):
            st.markdown(feats_html(character.feats), unsafe_allow_html=True)