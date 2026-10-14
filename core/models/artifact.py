from typing import Literal

from pydantic import BaseModel


class Artifact(BaseModel):
    kind: Literal["musicxml", "midi"]
    id: str
