import sentry_sdk
from sentry_sdk.integrations.httpx import HttpxIntegration

from config import settings


def setup_sentry(release: str) -> None:
    """Starts Sentry error tracking when SENTRY_DSN is set."""
    if settings.sentry_dsn is None:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn.get_secret_value(),
        environment=settings.environment,
        release=f"fastapi-census@{release}",
        send_default_pii=False,
        # Local variables can hold API keys, so they are never sent
        include_local_variables=False,
        # The httpx integration records request URLs, and those contain API keys
        disabled_integrations=[HttpxIntegration()],
    )
