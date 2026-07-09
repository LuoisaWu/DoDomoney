from difflib import SequenceMatcher
from typing import Any

from services.competitor_service import find_competitors


def _normalize(text: str) -> str:
    return " ".join(text.casefold().strip().split())


def match_target_game(query: str, games: list[dict[str, Any]]) -> tuple[dict[str, Any], bool, str]:
    normalized_query = _normalize(query)

    exact_candidates = [game for game in games if _normalize(game["name"]) in normalized_query]
    if exact_candidates:
        target = max(exact_candidates, key=lambda game: len(game["name"]))
        return target, True, f"已匹配到目标游戏 {target['name']}"

    best_game = None
    best_score = 0.0
    for game in games:
        name = _normalize(game["name"])
        score = SequenceMatcher(None, normalized_query, name).ratio()
        query_words = normalized_query.split()
        for size in range(1, min(len(query_words), 8) + 1):
            for start in range(len(query_words) - size + 1):
                phrase = " ".join(query_words[start : start + size])
                score = max(score, SequenceMatcher(None, phrase, name).ratio())
        if score > best_score:
            best_game, best_score = game, score

    if best_game and best_score >= 0.72:
        return best_game, True, f"已通过模糊匹配定位到目标游戏 {best_game['name']}"

    fallback = max(games, key=lambda game: (game["rating"], game["positive_rate"], game["review_count"]))
    return fallback, False, f"未匹配到明确的游戏名称，已默认选择评分最高的游戏 {fallback['name']}"


def _generate_swot(target: dict[str, Any], competitors: list[dict[str, Any]]) -> dict[str, list[str]]:
    platform = target["platform"]
    genre = target["genre"]
    audience = "、".join(target["target_users"][:2])
    strong_competitors = sum(game["rating"] >= target["rating"] for game in competitors)
    return {
        "strengths": target["advantages"],
        "weaknesses": target["disadvantages"],
        "opportunities": [
            f"可利用 {platform} 的多平台覆盖扩大用户触达范围",
            f"围绕 {genre} 核心玩法持续细分内容和社区运营",
            f"针对 {audience} 推出更精准的活动与长期内容更新",
        ],
        "threats": [
            f"当前样本中存在 {len(competitors)} 个高相似竞品，用户注意力竞争明显",
            f"有 {strong_competitors} 个主要竞品评分不低于目标游戏，同质化会放大口碑压力",
            "相近价格区间的促销竞争，以及版本更新造成的短期评价波动，可能影响转化",
        ],
    }


def analyze_query(query: str, games: list[dict[str, Any]]) -> dict[str, Any]:
    target, matched, message = match_target_game(query, games)
    competitors = find_competitors(target, games)
    top_names = "、".join(game["name"] for game in competitors[:3])
    top_score = competitors[0]["similarity_score"] if competitors else 0

    summary = (
        f"{target['name']} 是一款由 {target['developer']} 开发的 {target['genre']} 游戏，"
        f"覆盖 {target['platform']}，评分 {target['rating']}/10，好评率 {target['positive_rate']}%。"
        f"其核心体验包括{'、'.join(target['gameplay_features'][:3])}。"
    )
    comparison = (
        f"系统依据类型、标签、平台、价格和口碑指标筛选出 5 个主要竞品。"
        f"相似度靠前的产品为 {top_names}；最高相似度得分为 {top_score}。"
        f"{target['name']} 的优势集中在{'、'.join(target['advantages'][:2])}，"
        "建议持续观察头部竞品的内容更新、折扣和用户评价变化。"
    )
    market_position = (
        f"{target['name']} 位于 {target['genre']} 赛道，主要面向{'、'.join(target['target_users'])}。"
        f"以 {target['price']:.2f} 美元定价和 {target['positive_rate']}% 好评率来看，"
        "其市场位置由核心玩法辨识度、用户口碑与长期内容价值共同支撑。"
    )
    suggestions = [
        f"强化{'、'.join(target['gameplay_features'][:2])}等高辨识度玩法，并形成稳定的内容更新节奏。",
        f"针对{'、'.join(target['target_users'][:2])}开展分层运营，提升社区活跃和长期留存。",
        f"持续追踪 {top_names} 的价格、版本更新和评价变化，制定差异化促销与产品路线。",
    ]

    return {
        "matched": matched,
        "message": message,
        "target_game": target,
        "competitors": competitors,
        "comparison": comparison,
        "market_position": market_position,
        "swot": _generate_swot(target, competitors),
        "summary": summary,
        "suggestions": suggestions,
    }
