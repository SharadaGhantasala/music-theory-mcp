import pytest

from core.errors import (
    AnalysisError,
    InvalidIntervalError,
    InvalidNoteError,
    TheoryError,
    UnknownScaleError,
)


@pytest.mark.parametrize(
    "error", [InvalidNoteError, InvalidIntervalError, UnknownScaleError, AnalysisError]
)
def test_specific_errors_are_theory_errors(error):
    with pytest.raises(TheoryError):
        raise error("bad input")
