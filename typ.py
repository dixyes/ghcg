from typing import Any
import datetime

from pydantic import BaseModel, Field


# see https://github.com/grubersjoe/github-contributions-api
class Contribution(BaseModel):
    date: str  # ISO 8601 format date YYYY-MM-DD
    count: int
    level: int = Field(ge=0, le=4)  # Contribution level (0-4)


class DatedContribution(BaseModel):
    date: datetime.date
    count: int
    level: int = Field(ge=0, le=4)  # Contribution level (0-4)


class ContributionData(BaseModel):
    total: dict[str, int]
    contributions: list[Contribution]


class ColorFilamentLayer(BaseModel):
    """
    Represents a filament layer with a specific color and number of layers.

    For example:

    [
    ColorFilamentLayer(l = 2, c = "000000"),
    ColorFilamentLayer(l = 1, c = "00FF00"),
    ColorFilamentLayer(l = 1, c = "FFFFFF"),
    ]

    generates:

    black
    black
    green
    white
    background

    or

    black
    black
    green
    white
    auto background
    white
    green
    black
    black

    when symmetric
    """

    l: int  # layers
    c: str  # Hex color code for the filament


class Style:
    def __init__(
        self,
        workdir: str,
        params: str,
        toolPaths: dict[str, str],
        username: str,
    ):
        raise NotImplementedError("abstract")

    def generate(self, contribs: list[Contribution]) -> str:
        raise NotImplementedError("abstract")
