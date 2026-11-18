from html import escape

import streamlit as st

from final_proj_chatbot.pages.templates.character_ui import blocks, confirm_delete, portrait_html
from final_proj_chatbot.models.Character import Character
from final_proj_chatbot.models.CharacterRepository import get_character_repo
from final_proj_chatbot.routes import CREATE, DETAILS, go
from final_proj_chatbot.styles.style import inject_styles

st.set_page_config(
    page_title="Power Scaling - Characters ❤️‍🔥❤️‍🔥❤️‍🔥",
    layout="wide",
)
inject_styles()

CARDS_PER_ROW = 5

repo = get_character_repo()

# Deletes are carried out here, in a normal script run, so the LocalStorage
# write is rendered with the page (the confirm dialog only sets the flag).
pending_id = st.session_state.pop("pending_delete", None)
if pending_id:
    doomed = repo.get_character(pending_id)
    if doomed and repo.delete_character(pending_id):
        st.toast(f"Deleted {doomed.name}", icon=":material/delete:")


def render_card(character: Character) -> None:
    with st.container(key=f"char_card_{character.id}"):
        st.markdown(
            blocks(
                portrait_html(character.image, character.name),
                f'<div class="pw-card-name">{escape(character.name)}</div>',
                f'<div class="pw-card-origin">{escape(character.origin)}</div>',
            ),
            unsafe_allow_html=True,
        )
        if st.button(
            f"Open details for {character.name}",
            key=f"open_{character.id}",
            type="tertiary",
            width="stretch",
        ):
            go(DETAILS, character.id)
        _, delete_col = st.columns([4, 1], gap="small")
        if delete_col.button(
            "", icon=":material/delete:", key=f"del_{character.id}", help="Delete", width="stretch"
        ):
            confirm_delete(character.id, character.name)


characters = repo.get_all()

with st.container(key="page_head"):
    title_col, new_col = st.columns([4, 1], vertical_alignment="center")
    title_col.markdown(
        f'<div class="pw-pagehead">Characters <span class="pw-count">{len(characters)}</span></div>',
        unsafe_allow_html=True,
    )
    if new_col.button("New character", icon=":material/add:", type="primary", width="stretch"):
        go(CREATE)

if not characters:
    st.markdown(
        '<div class="pw-empty">No characters yet. Create your first one to start your collection.</div>',
        unsafe_allow_html=True,
    )
else:
    for start in range(0, len(characters), CARDS_PER_ROW):
        columns = st.columns(CARDS_PER_ROW, gap="small")
        for column, character in zip(columns, characters[start : start + CARDS_PER_ROW]):
            with column:
                render_card(character)