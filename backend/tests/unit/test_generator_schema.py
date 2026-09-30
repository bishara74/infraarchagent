import pytest
from pydantic import ValidationError

from app.agents.generators.schema import GeneratorOutput


@pytest.mark.req("FR-G-02")
def test_generator_output_defaults_notes_and_requires_text_files() -> None:
    output = GeneratorOutput.model_validate({"files": {"terraform/main.tf": "x"}})
    assert output.notes == ""
    assert output.files == {"terraform/main.tf": "x"}
    for invalid in ({"files": {}}, {"files": {"x": 7}}, {"files": []}):
        with pytest.raises(ValidationError):
            GeneratorOutput.model_validate(invalid)


@pytest.mark.req("FR-G-02")
def test_notes_length_and_extra_fields() -> None:
    assert (
        len(
            GeneratorOutput.model_validate(
                {"files": {"terraform/main.tf": "x"}, "notes": "n" * 1000}
            ).notes
        )
        == 1000
    )
    for invalid in (
        {"files": {"x": "y"}, "notes": "n" * 1001},
        {"files": {"x": "y"}, "unexpected": 1},
        {"files": {"x": "y"}, "notes": None},
    ):
        with pytest.raises(ValidationError):
            GeneratorOutput.model_validate(invalid)
