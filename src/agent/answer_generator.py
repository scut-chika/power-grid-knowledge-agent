import re

from src.rag_engine.siliconflow_client import chat_completion

SAFETY_NOTE = '本内容仅为运维知识参考，实际现场操作请严格遵守电网安全规程与现场作业规范'


def is_general_chat(query: str) -> bool:
    q = query.strip().lower()
    patterns = [
        r'^你好',
        r'^hi$',
        r'^hello$',
        r'你能做什么',
        r'你是谁',
        r'介绍一下你',
    ]
    return any(re.search(p, q) for p in patterns)


def build_llm_messages(query: str, refs: list[dict], attachment_excerpt: str | None = None) -> list[dict]:
    attach = ''
    if attachment_excerpt and attachment_excerpt.strip():
        excerpt = attachment_excerpt.strip()[:12000]
        attach = f"\n\n【用户本次附带的文档节选】\n{excerpt}\n"

    if refs:
        knowledge_blocks = []
        for index, reference in enumerate(refs[:8], start=1):
            metadata = reference.get('metadata') or {}
            source = reference.get('source') or metadata.get('file_name') or 'unknown'
            location = ''
            if metadata.get('page_number'):
                location = f"，第 {metadata['page_number']} 页"
            elif metadata.get('section'):
                location = f"，章节：{metadata['section']}"
            knowledge_blocks.append(
                f"[{index}] 来源：{source}{location}\n内容：{reference.get('content', '')}"
            )
        knowledge = '\n\n'.join(knowledge_blocks)
        prompt = (
            "你是电网运行知识助手。请严格基于给定知识片段回答，语言专业且简洁，"
            "并在对应结论后使用 [1]、[2] 格式标注来源。"
            "若证据不足，请明确说明缺少哪些信息；不得编造具体定值、设备状态或现场操作步骤。"
            f"{attach}\n\n用户问题：{query}\n\n知识片段：\n{knowledge}"
        )
    else:
        prompt = (
            "你是电网运行知识助手。用户在进行通用对话，请简洁回答并说明你可提供的能力："
            "设备信息查询、定值核对、巡检规程查询、故障处置流程查询、图纸文档检索。"
            f"{attach}\n\n用户问题：{query}"
        )

    return [
        {'role': 'system', 'content': '你是专业的电网运维智能助手。'},
        {'role': 'user', 'content': prompt},
    ]


def _generate_with_llm(query: str, refs: list[dict]) -> str | None:
    return chat_completion(messages=build_llm_messages(query, refs), temperature=0.2, max_tokens=800)


def fallback_answer(query: str, refs: list[dict]) -> str:
    if not refs:
        return (
            f'针对问题“{query}”，知识库中暂无直接相关信息。'
            '你可以尝试补充厂站、间隔、设备名称或定值项后重试。'
            f'\n\n{SAFETY_NOTE}'
        )
    lines = [f'针对问题“{query}”，基于知识库检索结果，结论如下：']
    for i, item in enumerate(refs[:5], start=1):
        lines.append(f"{i}. {item.get('content', '')}")
    lines.append('')
    lines.append(SAFETY_NOTE)
    return '\n'.join(lines)


def generate_answer(query: str, reasoning: dict, final_data: dict) -> tuple[str, list[dict]]:
    refs = final_data.get('results') or final_data.get('references') or []
    llm_answer = _generate_with_llm(query, refs[:8]) if (refs or is_general_chat(query)) else None

    if llm_answer:
        return f"{llm_answer}\n\n{SAFETY_NOTE}", refs[:5]

    answer = fallback_answer(query, refs)
    return answer, refs[:5]
