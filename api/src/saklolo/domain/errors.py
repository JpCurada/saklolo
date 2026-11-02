"""Domain errors. Adapters translate SDK exceptions into these."""


class SakloloError(Exception):
    """Base class for all Saklolo errors."""


class ServiceUnavailableError(SakloloError):
    """An external dependency (model, geocoder, database) could not be reached."""
