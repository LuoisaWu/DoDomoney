from typing import Any

from pydantic import BaseModel, Field


class Game(BaseModel):
    id: int
    name: str
    platform: str
    genre: str
    tags: list[str]
    developer: str
    publisher: str
    release_date: str
    price: float = Field(ge=0)
    rating: float = Field(ge=0, le=10)
    review_count: int = Field(ge=0)
    positive_rate: int = Field(ge=0, le=100)
    description: str
    gameplay_features: list[str]
    target_users: list[str]
    advantages: list[str]
    disadvantages: list[str]


class Competitor(Game):
    similarity_score: int
    match_reasons: list[str]


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class SWOT(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]


class ChatResponse(BaseModel):
    matched: bool
    message: str
    target_game: Game
    competitors: list[Competitor]
    comparison: str
    market_position: str
    swot: SWOT
    summary: str
    suggestions: list[str]


class GamesResponse(BaseModel):
    games: list[Game]


GameDict = dict[str, Any]
