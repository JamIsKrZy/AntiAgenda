import streamlit as st

from final_proj_chatbot.pages.character_form import render_character_form
from final_proj_chatbot.models.CharacterRepository import get_character_repo
from final_proj_chatbot.styles.style import inject_styles

st.set_page_config(
    page_title="Power Scaling - Character Build ❤️‍🔥❤️‍🔥❤️‍🔥",
    layout="wide",
)
inject_styles()

render_character_form(get_character_repo())