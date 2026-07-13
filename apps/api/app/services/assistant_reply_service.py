import re

from app.domain.schemas import AssistantPersonaRead, ParsedTransaction


class AssistantReplyService:
    def build_reply(self, parsed: ParsedTransaction, persona: AssistantPersonaRead) -> str:
        """Build an immediate persona-aware reply without a second model round-trip."""
        emoji_level = 0 if "不要使用表情" in persona.custom_instructions else persona.emoji_level
        emoji = " 🐾" if emoji_level >= 2 else (" ✓" if emoji_level == 1 else "")
        address_match = re.search(r"称呼我(?:为|叫)([^；;，,。\s]{1,12})", persona.custom_instructions)
        address = f"{address_match.group(1)}，" if address_match else ""
        if not parsed.is_complete:
            question = parsed.follow_up_question or self._follow_up(parsed.follow_up_fields[0])
            prefixes = {
                "cute": "还差一点点，",
                "rational": "信息不完整：",
                "encouraging": "马上就记好啦，",
                "balanced": "还需要补充：",
            }
            return f"{address}{prefixes[persona.mode.value]}{question}{emoji}"

        amount = f"{parsed.amount:.2f}".rstrip("0").rstrip(".")
        action = "收入" if parsed.type.value == "income" else "支出"
        prefixes = {
            "cute": "记好啦",
            "rational": "已记录",
            "encouraging": "做得好，已经记下",
            "balanced": "已经记下",
        }
        reply = f"{address}{prefixes[persona.mode.value]}：{action} ¥{amount}，分类为{parsed.category}。"
        if persona.snark_level >= 4 and parsed.type.value == "expense":
            reply += " 钱包已经收到这次行动报告。"
        if persona.reply_length in ("medium", "detailed") and parsed.description and parsed.description != parsed.category:
            reply += f" 备注：{parsed.description}。"
        if persona.reply_length == "detailed" and persona.proactive_insights:
            reply += " 我会在后续统计中持续关注这类收支。"
        return reply + emoji

    @staticmethod
    def _follow_up(field: str) -> str:
        return {
            "amount": "这笔是多少钱？",
            "category": "这笔钱主要花在什么地方？",
            "occurred_at": "这笔账是什么时候发生的？",
            "type": "这是收入还是支出？",
        }[field]
