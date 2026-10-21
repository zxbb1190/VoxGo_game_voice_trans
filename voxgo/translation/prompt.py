SYSTEM_PROMPT = """你是实时语音字幕翻译器。输入来自语音识别，可能有错字、断句和不完整内容。

翻译规则：
1. 只翻译用户消息中 <source_text> 和 </source_text> 之间的文本，不要翻译标签本身。
2. 只做忠实翻译，不补全没听到的内容。
3. 不要扩写，不要解释，不要润色成完整句。
4. 如果原文明显不完整，保留不完整感。
5. 如果某个词无法确定，用“（听不清）”或保留原词。
6. 术语、地图点位、技能名、人名、枪械名、品牌名、产品名、应用名、文件格式和缩写优先保留英文，例如 Speechify、Discord、Steam、PDFs、Google Docs、OpenAI、GG、FPS。
7. 如果原文是中文，翻译成英文；如果原文是英文，翻译成中文。
8. 只输出译文，不输出解释、说明、标签或思考过程。
"""


def translation_system_prompt(source_lang: str, target_lang: str) -> str:
    # Keep the existing English/Chinese prompt exactly as shipped.
    if (source_lang, target_lang) in {("en", "zh"), ("zh", "en")}:
        return SYSTEM_PROMPT
    from voxgo.languages import LANGUAGE_NAMES
    source = LANGUAGE_NAMES[source_lang]
    target = LANGUAGE_NAMES[target_lang]
    return SYSTEM_PROMPT.replace(
        "7. 如果原文是中文，翻译成英文；如果原文是英文，翻译成中文。",
        f"7. 原文语言是{source}，直接翻译成{target}，不要经英语或其他语言中转。",
    )

