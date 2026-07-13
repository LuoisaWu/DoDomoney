from app.domain.enums import AssistantTone
from app.domain.schemas import ParsedEntry


class AssistantReplyService:
    def build_reply(self, parsed: ParsedEntry, tone: AssistantTone) -> str:
        amount = f"{parsed.amount} 元"
        category = parsed.category

        templates = {
            AssistantTone.CUTE: f"账小喵记下啦：{category} {amount}。今天的钱包也在认真生活呢。",
            AssistantTone.SNARKY: f"已记录 {category} {amount}。账小喵不评价，但账本已经默默看见了。",
            AssistantTone.GENTLE: f"已经帮你记录好 {category} {amount}。慢慢来，清楚知道钱花在哪里就很棒。",
            AssistantTone.ADVISOR: f"已记录一笔{category}支出 {amount}。建议本周继续关注该分类累计金额。",
            AssistantTone.MINIMAL: f"已记录：{category} {amount}。",
        }
        return templates[tone]
