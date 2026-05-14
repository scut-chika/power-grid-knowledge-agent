def reason(plan: list[dict], tool_results: list[dict]) -> dict:
    steps = []
    for idx, (task, result) in enumerate(zip(plan, tool_results), start=1):
        steps.append({'step': idx, 'task': task['desc'], 'observation': '已执行', 'result_preview': str(result)[:200]})
    return {'steps': steps}
