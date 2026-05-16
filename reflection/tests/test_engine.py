"""复盘引擎测试（不依赖 LLM API）。"""
from reflection.engine import start_session, _dimension_key, _get_phase_prompt


def test_start_session():
    """验证 start_session 创建 session 并返回开场白。"""
    sid, opening = start_session(tag="测试")
    assert sid > 0
    assert "今天" in opening
    assert "什么在你心里" in opening


def test_dimension_key():
    """验证维度中文→英文映射。"""
    assert _dimension_key("念头") == "thought"
    assert _dimension_key("内在状态") == "state"
    assert _dimension_key("道的体悟") == "dao"
    assert _dimension_key("未知") == "thought"


def test_phase_prompt():
    """验证三轮提示词包含正确阶段标记。"""
    p1 = _get_phase_prompt(1)
    assert "倾倒" in p1

    p2 = _get_phase_prompt(3)
    assert "觉察" in p2

    p3 = _get_phase_prompt(6)
    assert "沉淀" in p3
