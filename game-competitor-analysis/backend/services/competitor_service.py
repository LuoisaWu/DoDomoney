import re
from typing import Any


def _tokens(value: str) -> set[str]:
    return {part.strip().casefold() for part in re.split(r"[/,|]", value) if part.strip()}


def calculate_similarity(target: dict[str, Any], candidate: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    if target["genre"].casefold() == candidate["genre"].casefold():
        score += 30
        reasons.append("游戏类型相近")

    common_tags = {tag.casefold() for tag in target["tags"]} & {tag.casefold() for tag in candidate["tags"]}
    if common_tags:
        score += len(common_tags) * 10
        reasons.append(f"存在 {len(common_tags)} 个相同标签")

    if _tokens(target["platform"]) & _tokens(candidate["platform"]):
        score += 10
        reasons.append("平台存在重叠")

    if abs(target["price"] - candidate["price"]) < 10:
        score += 10
        reasons.append("价格区间接近")

    if abs(target["rating"] - candidate["rating"]) < 0.5:
        score += 10
        reasons.append("评分接近")

    if abs(target["positive_rate"] - candidate["positive_rate"]) < 10:
        score += 10
        reasons.append("好评率接近")

    return score, reasons


def find_competitors(target: dict[str, Any], games: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    ranked = []
    for game in games:
        if game["id"] == target["id"]:
            continue
        score, reasons = calculate_similarity(target, game)
        ranked.append({**game, "similarity_score": score, "match_reasons": reasons})
    ranked.sort(key=lambda game: (game["similarity_score"], game["rating"], game["review_count"]), reverse=True)
    return ranked[:limit]
