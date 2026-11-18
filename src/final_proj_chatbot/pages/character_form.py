"""The character form, shared by the Create and Edit pages.

    render_character_form(repo)              -> create a new character
    render_character_form(repo, character)   -> edit an existing one

Edits are kept in a draft in session state and only written to the
repository when the person saves.
"""

import base64
import io

import streamlit as st
from PIL import Image, ImageOps

from final_proj_chatbot.pages.templates.character_ui import portrait_html
from final_proj_chatbot.models.Character import Character, CharacterFeat
from final_proj_chatbot.models.CharacterRepository import CharacterRepository
from final_proj_chatbot.routes import DETAILS, go

DEFAULT_POWER_LEVEL = 5


# ---------------------------------------------------------------------- draft
def _scope(character: Character | None) -> str:
    return f"edit_{character.id}" if character else "create"


def _blank_draft() -> dict:
    return {"name": "", "origin": "", "image": "", "power_ups": [], "feats": []}


def _draft_from(character: Character) -> dict:
    return {
        "name": character.name,
        "origin": character.origin,
        "image": character.image,
        "power_ups": list(character.power_ups),
        "feats": [CharacterFeat.from_dict(f.to_dict()) for f in character.feats],
    }


def _get_draft(scope: str, character: Character | None) -> dict:
    key = f"{scope}_draft"
    if key not in st.session_state:
        st.session_state[key] = _draft_from(character) if character else _blank_draft()
        st.session_state[f"{scope}_ver"] = 0  # bumped to give widgets a clean slate
    return st.session_state[key]


def discard_draft(character: Character) -> None:
    """Throws away unsaved edits (used by Cancel)."""
    scope = _scope(character)
    st.session_state.pop(f"{scope}_draft", None)
    st.session_state.pop(f"{scope}_ver", None)


def _wkey(scope: str, field: str) -> str:
    return f"{scope}_{field}_{st.session_state[f'{scope}_ver']}"


# ------------------------------------------------------------------- helpers
def image_to_data_uri(file, max_side: int = 480) -> str:
    """Shrinks the upload so it fits comfortably in browser LocalStorage."""
    img = ImageOps.exif_transpose(Image.open(file)).convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def resolve_feat(query: str) -> CharacterFeat:
    """Turns the search text into a feat. Swap this for a real lookup later."""
    return CharacterFeat(name=query, description=query, power_level=DEFAULT_POWER_LEVEL)


# ----------------------------------------------------------------- callbacks
def _sync_text(scope: str, field: str) -> None:
    st.session_state[f"{scope}_draft"][field] = st.session_state[_wkey(scope, field)]


def _set_portrait(scope: str) -> None:
    file = st.session_state.get(_wkey(scope, "portrait"))
    if file is not None:
        st.session_state[f"{scope}_draft"]["image"] = image_to_data_uri(file)


def _add_power_up(scope: str) -> None:
    value = st.session_state.get("new_power_up", "").strip()
    power_ups = st.session_state[f"{scope}_draft"]["power_ups"]
    if value and value not in power_ups:
        power_ups.append(value)


def _remove_power_up(scope: str, index: int) -> None:
    st.session_state[f"{scope}_draft"]["power_ups"].pop(index)


def _add_feat(scope: str) -> None:
    query = st.session_state.get("feat_query", "").strip()
    if query:
        st.session_state[f"{scope}_draft"]["feats"].append(resolve_feat(query))


def _remove_feat(scope: str, index: int) -> None:
    st.session_state[f"{scope}_draft"]["feats"].pop(index)


def _request_save(scope: str) -> None:
    # The LocalStorage write happens in the main script run, not in this callback
    st.session_state[f"{scope}_pending_save"] = True


# --------------------------------------------------------------------- save
def _commit(repo: CharacterRepository, scope: str, character: Character | None, draft: dict) -> None:
    name = draft["name"].strip()
    origin = draft["origin"].strip()

    if not name:
        if character is not None:
            st.toast("Enter a name for this character.", icon=":material/info:")
            return
        name = f"Character {len(repo.get_all()) + 1}"
    if not origin:
        st.toast("Add an origin to save this character.", icon=":material/info:")
        return

    fields = dict(
        image=draft["image"],
        power_ups=list(draft["power_ups"]),
        feats=list(draft["feats"]),
    )
    if character is None:
        repo.new_character(name=name, origin=origin, **fields)
        draft.update(_blank_draft())
        st.session_state[f"{scope}_ver"] += 1
        st.toast(f"Created {name}", icon=":material/check_circle:")
    else:
        repo.update_character(character.id, name=name, origin=origin, **fields)
        st.toast(f"Saved changes to {name}", icon=":material/check_circle:")


# --------------------------------------------------------------------- form
def render_character_form(repo: CharacterRepository, character: Character | None = None) -> None:
    scope = _scope(character)
    draft = _get_draft(scope, character)

    if st.session_state.pop(f"{scope}_pending_save", False):
        _commit(repo, scope, character, draft)

    left, right = st.columns([1, 2], gap="large")

    with left:
        with st.container(key="profile_card"):
            st.markdown(portrait_html(draft["image"], draft["name"]), unsafe_allow_html=True)
            with st.popover("Change portrait", icon=":material/image:", width="stretch"):
                st.file_uploader(
                    "Portrait",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=_wkey(scope, "portrait"),
                    on_change=_set_portrait,
                    args=(scope,),
                    label_visibility="collapsed",
                )

            st.text_input(
                "Name",
                value=draft["name"],
                key=_wkey(scope, "name"),
                placeholder=f"Character {len(repo.get_all()) + 1}" if character is None else "Name",
                on_change=_sync_text,
                args=(scope, "name"),
            )
            st.text_input(
                "Origin",
                value=draft["origin"],
                key=_wkey(scope, "origin"),
                placeholder="e.g. One Piece",
                on_change=_sync_text,
                args=(scope, "origin"),
            )

            st.markdown('<div class="pw-label">Power ups</div>', unsafe_allow_html=True)
            with st.container(horizontal=True, key="powerups_row"):
                for i, power_up in enumerate(draft["power_ups"]):
                    st.button(
                        f"{power_up}  ×",
                        key=f"power_up_{i}",
                        on_click=_remove_power_up,
                        args=(scope, i),
                        help="Remove",
                    )
                with st.popover("Add", icon=":material/add:"):
                    with st.form("power_up_form", clear_on_submit=True, border=False):
                        st.text_input(
                            "Power up",
                            key="new_power_up",
                            placeholder="e.g. Gear 5",
                            label_visibility="collapsed",
                        )
                        st.form_submit_button("Add power up", on_click=_add_power_up, args=(scope,))

            if character is None:
                st.button(
                    "Create character",
                    type="primary",
                    width="stretch",
                    on_click=_request_save,
                    args=(scope,),
                )
            else:
                cancel_col, save_col = st.columns(2)
                if cancel_col.button("Cancel", width="stretch"):
                    discard_draft(character)
                    go(DETAILS, character.id)
                save_col.button(
                    "Save changes",
                    type="primary",
                    width="stretch",
                    on_click=_request_save,
                    args=(scope,),
                )

    with right:
        with st.container(key="feats_card"):
            st.markdown('<div class="pw-title">Feats</div>', unsafe_allow_html=True)

            with st.container(height=380, border=False, key="feats_scroll"):
                if not draft["feats"]:
                    st.markdown(
                        '<div class="pw-empty">No feats yet. Search for one below and it will show up here.</div>',
                        unsafe_allow_html=True,
                    )
                for i, feat in enumerate(draft["feats"]):
                    with st.container(key=f"feat_card_{i}"):
                        text_col, remove_col = st.columns([14, 1], vertical_alignment="center")
                        text_col.write(feat.description)
                        remove_col.button(
                            "",
                            icon=":material/close:",
                            key=f"feat_x_{i}",
                            on_click=_remove_feat,
                            args=(scope, i),
                            help="Remove feat",
                        )

            with st.container(key="feat_bar"):
                with st.form("feat_form", clear_on_submit=True, border=False):
                    query_col, send_col = st.columns([14, 1], vertical_alignment="center")
                    query_col.text_input(
                        "Search feats",
                        key="feat_query",
                        placeholder="Search character greatest feats",
                        label_visibility="collapsed",
                    )
                    send_col.form_submit_button(
                        "", icon=":material/send:", on_click=_add_feat, args=(scope,)
                    )