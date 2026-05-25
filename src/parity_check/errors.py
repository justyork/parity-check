class ParityCheckError(Exception):
    """Base error for parity-check."""


class ConfigError(ParityCheckError):
    """Invalid or missing configuration."""


class RequestError(ParityCheckError):
    """HTTP request execution failed."""
