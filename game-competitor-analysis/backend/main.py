from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import get_all_games, get_game, initialize_database
from models import ChatRequest, ChatResponse, Game, GamesResponse
from services.analysis_service import analyze_query


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Game Competitor Analysis API",
    description="基于规则的多平台游戏竞品追踪与智能对标分析后端",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"message": "Game Competitor Analysis API is running", "docs": "/docs"}


@app.get("/api/games", response_model=GamesResponse, tags=["games"])
def list_games() -> dict[str, list[dict]]:
    return {"games": get_all_games()}


@app.get("/api/games/{game_id}", response_model=Game, tags=["games"])
def game_detail(game_id: int) -> dict:
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="游戏不存在")
    return game


@app.post("/api/chat", response_model=ChatResponse, tags=["analysis"])
def chat(request: ChatRequest) -> dict:
    return analyze_query(request.query, get_all_games())
