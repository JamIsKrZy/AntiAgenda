# routes.py
import streamlit as st

ARENA = st.Page("pages/arena.py", title="Arena", icon="👋", default=True)
CHARACTERS = st.Page("pages/character_list.py", title="Characters")
CREATE = st.Page("pages/create_character.py", title="Create")
DETAILS = st.Page(
    "pages/character_detail.py",
    title="Character Details",
    visibility="hidden",
)
EDIT = st.Page("pages/character_edit.py", title="Edit Character", visibility="hidden")

ALL_PAGES = [ARENA, CHARACTERS, CREATE, DETAILS, EDIT]


def go(page: st.Page, character_id: str | None = None) -> None:
    if character_id is None:
        st.session_state.pop("selected_character_id", None)
        st.switch_page(page)
        return

    st.session_state["selected_character_id"] = character_id
    st.switch_page(page, query_params={"id": character_id})


def selected_character_id() -> str | None:
    return st.query_params.get("id") or st.session_state.get("selected_character_id")