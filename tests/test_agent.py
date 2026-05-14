from src.agent.agent_core import run_agent


def test_agent_runs():
    out = run_agent('??XX????', session_id='test-session', user_id='admin')
    assert 'answer' in out
