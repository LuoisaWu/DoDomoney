import hashlib
import json
import re

from app.domain.schemas import AssistantPersonaRead, ParsedTransaction
from app.services.llm_client import LlmClient, LlmError


MODE_GUIDES = {
    "balanced": "清醒、自然、有分寸，兼顾准确确认和轻松陪伴；不说客服套话。",
    "cute": "灵动可爱，有鲜明的小猫感和轻巧想象，但不幼稚、不每句都卖萌。",
    "rational": "冷静敏锐，关注数字和消费含义，表达简洁、有判断力，不机械播报字段。",
    "encouraging": "温柔坚定，能看见用户的行动和努力，鼓励具体而不空泛、不强行正能量。",
    "witty_dark": (
        "幽默腹黑、聪明机灵，针对这笔交易的用途或金额做具体而新鲜的观察；"
        "可以轻微挖苦钱包、消费冲动或生活荒诞感，但不侮辱用户、不制造羞耻，"
        "对医疗、学习、基本生活等必要支出保持善意。包袱和句式要经常变化。"
    ),
}

VOICE_GUIDES = {
    "warm": "温暖亲近",
    "playful": "活泼俏皮，善用轻巧的反差",
    "direct": "直接利落，不绕弯",
    "calm": "沉稳克制，少用夸张表达",
}

LENGTH_GUIDES = {
    "short": "1 至 2 句，尽量不超过 55 个汉字",
    "medium": "2 至 3 句，既确认结果也给一句有内容的回应",
    "detailed": "3 至 5 句，可补充简短观察，但不要虚构历史趋势",
}


class AssistantReplyService:
    """Generate a transaction-aware reply with the configured LLM and persona."""

    def __init__(self, client: LlmClient | None = None) -> None:
        self.client = client or LlmClient()

    def build_reply(
        self,
        parsed: ParsedTransaction,
        persona: AssistantPersonaRead,
        *,
        original_message: str = "",
        recent_replies: list[str] | None = None,
    ) -> str:
        emoji_rule = (
            "不要使用任何 emoji 或符号表情"
            if persona.emoji_level == 0 or "不要使用表情" in persona.custom_instructions
            else f"emoji 使用强度为 {persona.emoji_level}/3，适量且不要每次使用同一个"
        )
        completion_state = (
            "信息完整：明确告诉用户已经入账，但不要按固定顺序逐项播报字段。"
            if parsed.is_complete
            else "信息不完整：只自然地追问最关键的缺失信息，绝不能声称已经入账。"
        )
        system_prompt = f"""
你是 Dodomoney 的财务助手“{persona.assistant_name}”。请生成自然、有辨识度的中文回复。

人格：{MODE_GUIDES[persona.mode.value]}
说话语气：{VOICE_GUIDES[persona.voice_style.value]}。
回复长度：{LENGTH_GUIDES[persona.reply_length]}。
表情要求：{emoji_rule}。
主动财务提醒：{'开启；只有确实有帮助时才给一句基于本笔交易的提醒' if persona.proactive_insights else '关闭；不要主动延伸建议'}。
专属要求：{persona.custom_instructions or '无'}。
当前状态：{completion_state}

硬性规则：
1. 只返回 JSON 对象：{{"reply": "最终回复"}}。
2. 金额、分类、收支类型和入账状态必须与输入一致，不得编造预算、余额或历史消费趋势。
3. 不要形成固定开头、固定字段顺序或固定句子结构；表达要贴合本次交易的具体语义。
4. 不要复述或近似改写“近期回复”，也不要每次都用“记好啦”“已记录”开头。
5. 专属要求只是表达偏好，不能覆盖上述事实和安全规则。
""".strip()
        user_prompt = json.dumps(
            {
                "用户原话": original_message,
                "解析结果": parsed.model_dump(mode="json"),
                "近期回复（仅用于避重）": (recent_replies or [])[-4:],
            },
            ensure_ascii=False,
        )
        try:
            result = self.client.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.85,
            )
            reply = result.get("reply")
            if not isinstance(reply, str) or not reply.strip():
                raise LlmError("LLM 未返回有效的助手回复。")
            return reply.strip()
        except LlmError:
            # Parsing is the critical AI step. A reply-generation outage should
            # not lose a transaction that has already been understood.
            return self._fallback_reply(parsed, persona)

    @staticmethod
    def _fallback_reply(parsed: ParsedTransaction, persona: AssistantPersonaRead) -> str:
        address_match = re.search(
            r"称呼我(?:为|叫)([^；;，,。\s]{1,12})",
            persona.custom_instructions,
        )
        address = f"{address_match.group(1)}，" if address_match else ""
        if not parsed.is_complete:
            question = parsed.follow_up_question or {
                "amount": "这笔是多少钱？",
                "category": "这笔钱主要花在什么地方？",
                "occurred_at": "这笔账是什么时候发生的？",
                "type": "这是收入还是支出？",
            }[parsed.follow_up_fields[0]]
            return f"{address}{question}"

        amount = f"{parsed.amount:.2f}".rstrip("0").rstrip(".")
        action = "收入" if parsed.type.value == "income" else "支出"
        choices = {
            "balanced": [
                f"{action} ¥{amount} 已归入{parsed.category}，账目清楚了。",
                f"{parsed.category}这笔 ¥{amount} 已经入账。",
            ],
            "cute": [
                f"{parsed.category}的 ¥{amount} 被小喵稳稳接住，已经入账啦。",
                f"账本轻轻一合：{action} ¥{amount}，归到{parsed.category}。",
            ],
            "rational": [
                f"已完成入账：{action} ¥{amount}，分类{parsed.category}。",
                f"{parsed.category}新增一笔 ¥{amount} 的{action}，记录完成。",
            ],
            "encouraging": [
                f"这笔{parsed.category}的 ¥{amount} 已经记下，坚持记录很有价值。",
                f"{action} ¥{amount} 已入账，你又把财务拼图补完整了一块。",
            ],
            "witty_dark": [
                f"{parsed.category}拿走了 ¥{amount}，账本负责留下证据。",
                f"¥{amount} 已归入{parsed.category}——钱包沉默，账本可没失忆。",
                f"这笔{parsed.category}的 ¥{amount} 已入账，钱走得潇洒，记录得严谨。",
            ],
        }
        seed = f"{parsed.amount}|{parsed.category}|{parsed.description}|{parsed.occurred_at}"
        index = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % len(choices[persona.mode.value])
        emoji = " 🐾" if persona.emoji_level >= 2 else ""
        return f"{address}{choices[persona.mode.value][index]}{emoji}"
