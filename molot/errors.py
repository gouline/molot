class _TargetError(Exception):
    """Error relating to a target."""

    def __init__(self, name: str):
        self.name = name


class TargetNotFoundError(_TargetError):
    """Requested target not found."""


class TargetCircularDependencyError(_TargetError):
    """Circular dependency detected while evaluating target."""


class ShellReturnError(Exception):
    """Error for failed shell commands in piped mode."""

    def __init__(self, code: int, output: str):
        self.code = code
        self.output = output
