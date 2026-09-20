import pytest

from src import HeadingChunker


def test_sections_stay_separate_and_preserve_preamble():
    text = "Introduction.\n\n# Returns\nFirst rule.\n\n## Fees\nSecond rule."
    assert HeadingChunker().chunk(text) == [
        "Introduction.", "# Returns\n\nFirst rule.", "## Fees\n\nSecond rule."
    ]


def test_long_section_keeps_heading_and_all_content_within_limit():
    heading = "## Refund deadline"
    body = "abcdefghijklmnopqrstuvwxyz" * 5
    chunks = HeadingChunker(chunk_size=40).chunk(heading + "\n" + body)
    prefix = heading + "\n\n"
    assert len(chunks) > 1
    assert all(c.startswith(prefix) and len(c) <= 40 for c in chunks)
    assert "".join(c[len(prefix):] for c in chunks) == body


@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_headings_inside_fenced_code_do_not_start_sections(fence):
    text = f"# Policy\n{fence}\n## Example, not a section\n{fence}\nText.\n# Next\nRule."
    chunks = HeadingChunker().chunk(text)
    assert len(chunks) == 2
    assert "## Example, not a section" in chunks[0]
    assert chunks[1] == "# Next\n\nRule."


def test_empty_heading_only_and_plain_text():
    chunker = HeadingChunker(chunk_size=10)
    assert chunker.chunk(" \n") == []
    assert chunker.chunk("# A\n## B") == ["# A", "## B"]
    assert chunker.chunk("abcdefghijk") == ["abcdefghij", "k"]


def test_rejects_invalid_size_and_heading_without_content_budget():
    with pytest.raises(ValueError):
        HeadingChunker(chunk_size=0)
    with pytest.raises(ValueError):
        HeadingChunker(chunk_size=6).chunk("# Long\nBody")
