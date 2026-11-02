"""Domain errors. Adapters translate SDK exceptions into these."""


class SakloloError(Exception):
    """Base class for all Saklolo errors."""


class ServiceUnavailableError(SakloloError):
    """An external dependency (model, geocoder, database) could not be reached."""


class ModelOutputError(SakloloError):
    """A model returned no output, or output that doesn't match the requested schema."""


class PipelineError(SakloloError):
    """The triage pipeline did not complete for a message."""
