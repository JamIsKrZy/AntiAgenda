import streamlit as st

from final_proj_chatbot.pages.character_form import discard_draft, render_character_form
from final_proj_chatbot.pages.templates.character_ui import render_not_found
from final_proj_chatbot.models.CharacterRepository import get_character_repo
from final_proj_chatbot.routes import DETAILS, go, selected_character_id
from final_proj_chatbot.styles.style import inject_styles

st.set_page_config(
    page_title="Power Scaling - Edit Character ❤️‍🔥❤️‍🔥❤️‍🔥",
    layout="wide",
)
inject_styles()

repo = get_character_repo()

character = repo.get_character(selected_character_id())
if character is None:
    render_not_found()
    st.stop()

if st.button("Details", icon=":material/arrow_back:", type="tertiary"):
    discard_draft(character)
    go(DETAILS, character.id)

render_character_form(repo, character)