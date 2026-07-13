from app.domain.enums import EntryType


class CategoryService:
    def infer_category(self, text: str, entry_type: EntryType) -> tuple[str, str | None]:
        lowered = text.lower()

        if entry_type == EntryType.INCOME:
            if any(word in lowered for word in ["工资", "奖金", "salary"]):
                return "工资", "工资"
            if any(word in lowered for word in ["兼职", "项目", "part-time"]):
                return "兼职", "兼职"
            return "其他收入", "其他"

        if any(word in lowered for word in ["奶茶", "咖啡", "瑞幸", "星巴克", "饮料"]):
            return "餐饮", "饮品"
        if any(word in lowered for word in ["早餐", "午饭", "午餐", "晚饭", "晚餐", "火锅", "外卖"]):
            return "餐饮", None
        if any(word in lowered for word in ["打车", "地铁", "公交", "机票", "火车"]):
            return "交通出行", None
        if any(word in lowered for word in ["服务器", "课程", "书", "软件", "办公"]):
            return "学习办公", None
        if any(word in lowered for word in ["电影", "游戏", "会员", "腾讯视频", "爱奇艺"]):
            return "娱乐", None
        return "其他支出", "其他"
