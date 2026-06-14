"""Shim — ``src.core`` re-exports the re-homed governance core from ``ontowiz_core``.

The implementation now lives in ``packages/ontowiz-core/ontowiz_core`` (Tier B,
ADR-012/ADR-015). This shim keeps the legacy app (src/api, src/knowledge,
src/reasoning) and its tests working unchanged after the re-home. New code
should import from ``ontowiz_core`` directly.
"""

from ontowiz_core import *  # noqa: F401,F403
from ontowiz_core import __all__  # noqa: F401
