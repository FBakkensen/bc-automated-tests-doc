from pdf2md.utils import deterministic_slug, repair_hyphenation, is_heading_candidate

def test_deterministic_slug():
    assert deterministic_slug("Hello World", prefix_index=1) == "01-hello-world"
    assert deterministic_slug("Hello World", prefix_index=12) == "12-hello-world"


def test_repair_hyphenation_basic():
    lines = ["inter-", "esting", "normal line", "code-", "Block"]
    repaired = repair_hyphenation(lines)
    assert "interesting" in repaired
    assert any("code-Block" == l for l in repaired)


def test_is_heading_candidate():
    assert is_heading_candidate("Chapter 3 Architecture")
    assert is_heading_candidate("PART I OVERVIEW")
    assert not is_heading_candidate("This is a long paragraph that should not be a heading because it exceeds the reasonable length and lacks structure")
