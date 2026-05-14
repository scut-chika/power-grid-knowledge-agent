def assemble_context(query: str, knowledge_items: list[dict], max_tokens: int = 4096) -> str:
    sections = [
        'You are a power-grid assistant. Answer strictly from the provided knowledge. If insufficient, say knowledge not found.',
        f'User query: {query}',
        'Knowledge snippets:',
    ]

    total = 0
    for idx, item in enumerate(knowledge_items, start=1):
        block = f"[{idx}] source: {item.get('source', 'unknown')}\ncontent: {item.get('content', '')}\n"
        total += len(block)
        if total > max_tokens * 2:
            break
        sections.append(block)

    return '\n'.join(sections)
