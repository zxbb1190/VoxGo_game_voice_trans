"""Conservative, opt-in game phrase normalization.

Only exact normalized commands/templates are rewritten; ordinary prose stays
untouched. This avoids changing words such as ``hold`` or ``one shot`` out of
context. The model remains responsible for free-form translation.
"""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class GlossaryPlan:
    normalized_text: str
    corrections: tuple = ()
    translated_override: str = ""


def _key(text):
    return re.sub(r"[\s,，。.!！?？:：;；]+", " ", (text or "").strip().casefold()).strip()

# Complete utterances only: source -> natural model-friendly text / exact answer.
_EN_ZH = {
    "go": "走", "go go": "快走", "push": "压上", "push now": "现在压上",
    "fall back": "撤退", "retreat": "撤退", "hold here": "守在这里",
    "hold this angle": "守住这个角度", "wait": "等一下", "follow me": "跟我来",
    "on me": "在我这里", "behind us": "在我们后面", "left": "左边",
    "right": "右边", "mid": "中路", "enemy": "敌人", "enemy spotted": "发现敌人",
    "two enemies": "两个敌人", "one shot": "一枪就死", "knocked": "倒地了",
    "revive me": "救我",  "cover me": "掩护我",
    "need healing": "我需要治疗", "i need healing": "我需要治疗",
    "reloading": "我在换弹", "reload": "换弹", "cover": "掩护",
    "nice try": "打得不错", "good game": "打得好", "gg": "打得好",
    "loot here": "这里有战利品", "take the loot": "拿走战利品",
    "armor broken": "护甲打碎了", "low health": "血量很低", "watch the flank": "小心侧翼",
    "rotate": "转移", "third party": "第三方队伍来了", "drop": "空投",
}
_ZH_EN = {
    "走": "Go", "快走": "Go go", "压上": "Push", "现在压上": "Push now",
    "撤退": "Fall back", "守在这里": "Hold here", "守住这个角度": "Hold this angle",
    "等一下": "Wait", "跟我来": "Follow me", "在我这里": "On me", "在我们后面": "Behind us",
    "左边": "Left", "右边": "Right", "中路": "Mid", "敌人": "Enemy", "发现敌人": "Enemy spotted",
    "两个敌人": "Two enemies", "一枪就死": "One shot", "倒地了": "Knocked",
    "救我": "Help me", "掩护我": "Cover me", "我需要治疗": "I need healing",
    "治疗": "Healing", "换弹": "Reloading", "换弹中": "Reloading",
    "小心侧翼": "Watch the flank", "转移": "Rotate", "空投": "Drop",
    "护甲打碎了": "Armor broken", "血量很低": "Low health", "第三方队伍来了": "Third party",
}
_SPECIAL_ZH_EN = {
    "我换子弹你帮我架一下": "I'm reloading. Cover me.",
    "我在换弹你帮我架一下": "I'm reloading. Cover me.",
    "我换弹你帮我架一下": "I'm reloading. Cover me.",
    "我倒地了救我": "I'm knocked. Revive me.",
    "我需要治疗掩护我": "I need healing. Cover me.",
}
_SPECIAL_EN_ZH = {
    "im reloading cover me": "我在换弹，掩护我。",
    "i'm reloading cover me": "我在换弹，掩护我。",
    "im knocked revive me": "我倒地了，救我。",
}

# Ambiguous single words never trigger an override without combat context.
for _ambiguous in ("hold", "one shot", "knocked", "cover", "drop", "third party", "rotate"):
    _EN_ZH.pop(_ambiguous, None)
for _ambiguous in ("救我", "转移", "倒地了", "空投"):
    _ZH_EN.pop(_ambiguous, None)

_PAIRS = (
    ("帮我拉枪线", "Draw enemy fire away from me"),
    ("开枪时压枪", "Control the recoil when firing"),
    ("先别舔包", "Don't loot the body yet"),
    ("我倒地了扶我", "I'm knocked down. Revive me"),
    ("补掉倒地的敌人", "Finish off the downed enemy"),
    ("附近有敌人的脚步声", "Enemy footsteps nearby"),
    ("我正在装弹", "I'm reloading"),
    ("我残血了", "I'm low on health"),
    ("探头看一下敌人", "Peek at the enemy"),
    ("晃身探一下敌人", "Jiggle peek the enemy"),
    ("提前开枪压住门口", "Prefire the doorway"),
    ("形成交叉火力", "Set up crossfire"),
    ("火力压制敌人", "Suppress the enemy"),
    ("帮队友补掉击杀者", "Trade the kill for our teammate"),
    ("救起倒地的队友", "Revive the downed teammate"),
    ("击倒那个敌人", "Knock down that enemy"),
    ("朝敌人扔手雷", "Throw grenades at the enemy"),
    ("往安全区转点", "Rotate into the safe zone"),
    ("我在换弹", "I'm reloading"), ("我正在换子弹", "I'm reloading"),
    ("你帮我架一下", "Cover me"), ("帮我架枪", "Cover me"),
    ("架住这个角度", "Hold this angle"), ("敌人在我们后面", "Enemies behind us"),
    ("敌人在左边", "Enemies on the left"), ("敌人在右边", "Enemies on the right"),
    ("敌人在楼上", "Enemies upstairs"), ("敌人在楼下", "Enemies downstairs"),
    ("敌人在屋顶", "Enemies on the roof"), ("敌人在桥对面", "Enemies across the bridge"),
    ("绕到敌人后面", "Flank the enemy"), ("别暴露位置", "Don't reveal our position"),
    ("保持隐蔽", "Stay hidden"), ("蹲下移动", "Move while crouching"),
    ("趴下", "Go prone"), ("找掩体", "Find cover"), ("待在掩体后面", "Stay behind cover"),
    ("扔烟雾弹", "Throw a smoke grenade"), ("扔闪光弹", "Throw a flashbang"),
    ("扔手雷", "Throw a grenade"), ("小心手雷", "Watch out for grenades"),
    ("别开枪", "Don't shoot"), ("停止射击", "Cease fire"), ("集中火力", "Focus fire"),
    ("瞄准头部", "Aim for the head"), ("我没有弹药了", "I'm out of ammo"),
    ("我需要弹药", "I need ammo"), ("我需要护甲", "I need armor"),
    ("我需要急救包", "I need a first aid kit"), ("我在打药", "I'm healing"),
    ("我在补甲", "I'm repairing my armor"), ("敌人残血了", "The enemy is low on health"),
    ("敌人倒地了", "The enemy is knocked down"), ("我倒地了", "I'm knocked down"),
    ("复活队友", "Revive our teammate"), ("别补枪", "Don't finish them off"),
    ("安全区在缩小", "The safe zone is shrinking"), ("先进安全区", "Get into the safe zone first"),
    ("往圈里走", "Move into the safe zone"), ("别进毒圈", "Stay out of the damage zone"),
    ("搜一下这栋楼", "Loot this building"), ("标记敌人位置", "Mark the enemy position"),
    ("标记弹药", "Mark the ammo"), ("队伍集合", "Regroup with the squad"),
    ("别单独行动", "Don't go alone"), ("等队友到齐", "Wait for the whole squad"),
)
for _zh, _en in _PAIRS:
    _ZH_EN[_key(_zh).replace(" ", "")] = _en
    _EN_ZH[_key(_en)] = _zh

# Split only when every character belongs to a curated command. Longest-first
# matching avoids accepting a familiar substring inside ordinary sentences.
def _chinese_commands(text):
    compact = _key(text).replace(" ", "")
    terms = sorted(_ZH_EN, key=len, reverse=True)
    def split(offset, parts):
        if offset == len(compact):
            return parts
        if len(parts) >= 6:
            return None
        for term in terms:
            if compact.startswith(term, offset):
                result = split(offset + len(term), parts + [(term, _ZH_EN[term])])
                if result:
                    return result
        return None
    return split(0, []) if len(compact) <= 160 else None


def preprocess(text, source, target):
    """Return a safe translation plan. Inputs outside en↔zh pass unchanged."""
    text = text or ""
    source, target = (source or "").lower(), (target or "").lower()
    # Questions and quoted language are not issued commands.
    if any(mark in text for mark in ("?", "？", "吗", "么", "“", "”", '"', "‘", "’")):
        return GlossaryPlan(text)
    if source == "zh" and target == "en":
        table, special = _ZH_EN, _SPECIAL_ZH_EN
    elif source == "en" and target == "zh":
        table, special = _EN_ZH, _SPECIAL_EN_ZH
    else:
        return GlossaryPlan(text)
    key = _key(text).replace(" ", "") if source == "zh" else _key(text)
    answer = special.get(key) or table.get(key)
    if answer:
        return GlossaryPlan(text, ((text, answer),), answer)
    if source == "zh":
        commands = _chinese_commands(text)
        if commands and len(commands) > 1:
            answer = ". ".join(target.rstrip(".!") for _, target in commands) + "."
            return GlossaryPlan(text, tuple(commands), answer)
        # Explicit first-person progressive reload phrase only; do not match a
        # negated statement, question, quotation, or a different subject.
        match = re.fullmatch(r"我正在换子弹([，,].+)?[。.]?", text.strip())
        if match and not any(mark in text for mark in ("?", "？", "吗", "么", "“", "”", '"', "不", "没")):
            normalized = text.replace("我正在换子弹", "我正在重新装填弹药", 1)
            return GlossaryPlan(normalized, (("reload_first_person", "reloading"),))
    normalized = text
    corrections = []
    if source == "zh":
        # These expressions identify combat actions; keep surrounding subjects,
        # negation and clauses intact. Avoid ambiguous single words such as 救/架.
        replacements = (
            ("换子弹", "重新装填弹药"), ("换弹", "重新装填弹药"),
            ("舔包", "搜刮战利品"), ("不是残血", "生命值并不低"),
            ("残血", "生命值很低"), ("满血", "生命值全满"),
            ("补甲", "修复护甲"), ("封烟", "投掷烟雾弹遮挡视线"),
            ("拉枪线", "移动到另一个射击角度"), ("压枪", "控制枪械后坐力"),
            ("有脚步", "有脚步声"),
        )
        for term, replacement in replacements:
            if term in normalized:
                normalized = normalized.replace(term, replacement)
                corrections.append((term, replacement))
    else:
        replacements = (
            (r"\bhold (this|the|that) angle\b", r"guard \1 shooting angle"),
            (r"\blow on health\b", "low on health"),
            (r"\bmedkit\b", "first aid kit"),
        )
        for pattern, replacement in replacements:
            updated = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
            if re.search(pattern, normalized, flags=re.IGNORECASE):
                corrections.append((pattern, replacement))
                normalized = updated
    if source == "en" and re.match(r"^I (?:am|\'m) low on health[.!，, ]", text.strip(), re.IGNORECASE):
        corrections.append(("first_person_low_health", "血量很低"))
    return GlossaryPlan(normalized, tuple(corrections))


def postprocess(translated, plan):
    """Apply only the explicit plan; currently model output is otherwise untouched."""
    if plan.translated_override:
        return plan.translated_override
    if ("reload_first_person", "reloading") in plan.corrections:
        translated = re.sub(r"\bI am changing (?:the |my )?bullets\b", "I am reloading", translated, flags=re.IGNORECASE)
        translated = re.sub(r"\bI'm changing (?:the |my )?bullets\b", "I'm reloading", translated, flags=re.IGNORECASE)
    terms = {term for term, _ in plan.corrections}
    if "舔包" in terms:
        translated = re.sub(r"\b(?:scratch|scrape|lick) (?:the )?(?:booty|loot|bag)\b", "loot", translated, flags=re.IGNORECASE)
    if "满血" in terms:
        translated = re.sub(r"\b(My|Your|His|Her|Our|Their) life is full\b", r"\1 health is full", translated, flags=re.IGNORECASE)
    if "不是残血" in terms:
        translated = re.sub(r"\b(He's|She's|I'm|You're|They're|We're) not a low-value (?:man|woman|person)\b", r"\1 not low on health", translated, flags=re.IGNORECASE)
    if "first_person_low_health" in terms:
        translated = re.sub(r"^我身体不好", "我血量很低", translated, count=1)
    return translated


def glossary_terms(source="", target=""):
    if source == "zh" and target == "en": return dict(_ZH_EN)
    if source == "en" and target == "zh": return dict(_EN_ZH)
    return {}
