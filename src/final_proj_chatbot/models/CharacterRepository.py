from typing import Any
import streamlit as st
from streamlit_local_storage import LocalStorage
from .Character import Character


class CharacterRepository:
    """Black box managing character state and browser LocalStorage sync."""

    STORAGE_KEY = "character_list"

    def __init__(self):
        self._storage = LocalStorage()
        self._characters: dict[str, Character] = {}
        self._hydrated = False

    def sync_from_storage(self) -> None:
        """
        Hydrates from browser LocalStorage once the component has mounted.
        Skips overwriting storage if getItem() returns None on initial render.
        """
        if self._hydrated:
            return

        raw_data = self._storage.getItem(self.STORAGE_KEY)
        if raw_data is None:
            return

        if isinstance(raw_data, dict):
            self._characters = {
                char_id: Character.from_dict(char_dict)
                for char_id, char_dict in raw_data.items()
            }
        self._hydrated = True

    def _save_to_storage(self) -> None:
        """Serializes internal Character objects to JSON-safe dicts for LocalStorage."""
        serialized = {
            char_id: char_obj.to_dict()
            for char_id, char_obj in self._characters.items()
        }
        self._storage.setItem(self.STORAGE_KEY, serialized)
        self._hydrated = True

    def new_character(self, name: str, origin: str, **kwargs: Any) -> Character:
        """Creates a new character, saves to LocalStorage, and returns it."""
        character = Character(name=name, origin=origin, **kwargs)
        while character.id in self._characters:
            character.new_id()

        self._characters[character.id] = character
        self._save_to_storage()
        return character

    def update_character(self, character_id: str, **updates: Any) -> Character:
        """
        Dynamically updates any valid attribute(s) on a Character
        (e.g. repo.update_character(id, name="Aria", level=5)) and syncs to storage.
        """
        character = self._characters.get(character_id)
        if not character:
            raise ValueError(f"Character with ID {character_id} not found")

        for attr, value in updates.items():
            if not hasattr(character, attr):
                raise AttributeError(f"Character has no attribute '{attr}'")
            if value is not None:
                setattr(character, attr, value)

        self._save_to_storage()
        return character

    def delete_character(self, character_id: str) -> bool:
        """Deletes a character by ID and syncs to storage."""
        if character_id in self._characters:
            del self._characters[character_id]
            self._save_to_storage()
            return True
        return False

    def save(self) -> None:
        """
        Explicit save helper if you mutate a Character directly
        (e.g., character.add_feat(...) or character.add_power_up(...)).
        """
        self._save_to_storage()

    def get_character(self, character_id: str) -> Character | None:
        return self._characters.get(character_id)

    def get_all(self) -> list[Character]:
        return list(self._characters.values())


def get_character_repo() -> CharacterRepository:
    """
    Ensures CharacterRepository is initialized once per session and
    hydrates from browser LocalStorage as soon as the component is ready.
    """
    if "character_repo" not in st.session_state:
        st.session_state["character_repo"] = CharacterRepository()

    repo: CharacterRepository = st.session_state["character_repo"]
    repo.sync_from_storage()
    return repo