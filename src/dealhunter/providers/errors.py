class ProviderError(RuntimeError):
    pass


class ProviderBlockedError(ProviderError):
    pass


class ProviderParseError(ProviderError):
    pass
