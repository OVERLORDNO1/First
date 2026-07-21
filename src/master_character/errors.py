from __future__ import annotations


class ProviderError(Exception):
    """Base class for cognition-provider failures."""

    category: str = "provider_error"

    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class UnknownModelPricingError(ProviderError):
    category = "unknown_model_pricing"


class TaskBudgetExceededError(ProviderError):
    category = "task_budget_exceeded"


class ProviderHTTPError(ProviderError):
    category = "http_error"

    def __init__(self, message: str, *, status_code: int, retryable: bool, attempts: int = 1):
        super().__init__(message, retryable=retryable)
        self.status_code = status_code
        self.attempts = attempts


class ProviderTimeoutError(ProviderError):
    category = "timeout"


class ProviderResponseError(ProviderError):
    """Malformed or undecodable provider response body."""

    category = "malformed_response"


class StructuredResultError(ProviderError):
    """The model never produced a valid structured result."""

    category = "invalid_structured_result"


class MaxTurnsExceededError(ProviderError):
    category = "max_turns_exceeded"


class ZeroCostUsageError(ProviderError):
    """A successful live call recorded zero cost; the ledger cannot be trusted."""

    category = "zero_cost_usage"
