"""Errors raised by the core theory library."""


class TheoryError(Exception):
    """Base class for all errors the core raises on bad input or failed analysis."""


class InvalidNoteError(TheoryError):
    """A note, pitch, or interval string could not be parsed."""


class UnknownScaleError(TheoryError):
    """The requested scale or mode type is not supported."""


class AnalysisError(TheoryError):
    """Analysis could not be completed, for example an unidentifiable chord."""


class InvalidIntervalError(TheoryError):
    """An interval name could not be parsed or does not exist, such as a "perfect third"."""
