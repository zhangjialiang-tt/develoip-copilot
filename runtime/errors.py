class ContractError(Exception):
    """A deterministic rejection or persistence contract failure."""

    def __init__(self, code: str, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class PersistenceError(ContractError):
    pass
