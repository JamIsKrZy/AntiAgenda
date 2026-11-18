import inspect
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CharacterFeat:
    name: str
    description: str
    power_level: int
    # Add any new fields here with defaults—no need to touch to_dict() or from_dict()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CharacterFeat":
        valid_keys = inspect.signature(cls).parameters
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class Character:
    name: str
    origin: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    image: str = ""
    power_ups: list[str] = field(default_factory=list)
    feats: list[CharacterFeat] = field(default_factory=list)
    # Add any new properties here with a default value, e.g.:
    # level: int = 1

    def new_id(self) -> str:
        self.id = str(uuid.uuid4())
        return self.id

    def add_power_up(self, power_up: str) -> None:
        self.power_ups.append(power_up)

    def add_feat(self, feat: CharacterFeat) -> None:
        self.feats.append(feat)

    def to_dict(self) -> dict[str, Any]:
        # Automatically converts self AND all nested CharacterFeat objects to dicts
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Character":
        # Only pass keys that exist on Character (prevents crashes if schema changes)
        valid_keys = inspect.signature(cls).parameters
        filtered = {k: v for k, v in data.items() if k in valid_keys}

        # Rehydrate nested CharacterFeat objects
        if "feats" in filtered:
            filtered["feats"] = [
                f if isinstance(f, CharacterFeat) else CharacterFeat.from_dict(f)
                for f in filtered["feats"]
            ]

        return cls(**filtered)