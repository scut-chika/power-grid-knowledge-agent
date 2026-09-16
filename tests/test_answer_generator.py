from src.agent.answer_generator import build_llm_messages


def test_prompt_includes_source_location_and_citation_instruction():
    messages = build_llm_messages(
        '如何检查保护动作？',
        [
            {
                'content': '先核对告警与故障录波。',
                'source': '保护规程.pdf',
                'metadata': {'page_number': 7},
            }
        ],
    )

    prompt = messages[-1]['content']
    assert '保护规程.pdf，第 7 页' in prompt
    assert '使用 [1]、[2] 格式标注来源' in prompt
    assert '不得编造具体定值' in prompt
