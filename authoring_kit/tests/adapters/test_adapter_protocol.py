from __future__ import annotations

import pytest
from pydantic import ValidationError

from ontowiz_authoring.adapters import AdapterRequest


@pytest.mark.contract
def test_adapter_request_rejects_unknown_operations_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        AdapterRequest.model_validate(
            {
                "format": "ontowiz-adapter-request",
                "format_version": 1,
                "request_id": "REQ-001",
                "workspace_id": "brand-variance",
                "expected_revision": 0,
                "command": {"operation": "activate"},
                "credential": "must-never-enter-the-transcript",
            }
        )
