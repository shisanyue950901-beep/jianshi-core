from dataclasses import dataclass

@dataclass(frozen=True)
class SourcePolicy:
    code: str
    status: str
    auto_collect: bool
    redisplay_allowed: bool

class SourceGateError(RuntimeError):
    pass

def assert_auto_collect_allowed(policy: SourcePolicy) -> None:
    if policy.status != "GREEN" or not policy.auto_collect:
        raise SourceGateError(
            f"AUTO_COLLECT_FORBIDDEN: source={policy.code} status={policy.status} auto_collect={policy.auto_collect}"
        )
