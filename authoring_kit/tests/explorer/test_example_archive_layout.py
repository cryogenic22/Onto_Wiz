from __future__ import annotations

import re
from collections.abc import Callable

import pytest

from examples.generate import WorkedSlice, build_brand_slice, build_mr_slice, slice_files
from ontowiz_authoring.explorer import CandidateExplorerContext

PACK_DOCUMENT = re.compile(
    r"pack/(?:scope|ontology|metrics|methods|policies|retrieval|"
    r"workflows|tools|evaluations|governance)/"
    r"[A-Za-z0-9][A-Za-z0-9._-]*\.(?:json|yaml)"
)


@pytest.mark.parametrize("builder", (build_brand_slice, build_mr_slice))
def test_worked_slice_uses_exact_candidate_archive_layout(
    builder: Callable[[], WorkedSlice],
) -> None:
    worked = builder()
    files = slice_files(worked)
    pack_files = {path: payload for path, payload in files.items() if path.startswith("pack/")}
    context = CandidateExplorerContext.model_validate_json(files["context-model.json"])

    assert "pack/pack.yaml" in pack_files
    assert all(
        path == "pack/pack.yaml" or PACK_DOCUMENT.fullmatch(path)
        for path in pack_files
    )
    assert context.manifest == worked.manifest
    assert {document.path for document in context.documents} == set(pack_files)


@pytest.mark.parametrize("builder", (build_brand_slice, build_mr_slice))
def test_worked_slice_renders_from_deserialized_emitted_context(
    builder: Callable[[], WorkedSlice],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[bytes] = []
    original = CandidateExplorerContext.model_validate_json

    def spy(
        cls: type[CandidateExplorerContext],
        payload: str | bytes | bytearray,
        *args: object,
        **kwargs: object,
    ) -> CandidateExplorerContext:
        del cls
        calls.append(bytes(payload) if not isinstance(payload, str) else payload.encode())
        return original(payload, *args, **kwargs)

    monkeypatch.setattr(
        CandidateExplorerContext,
        "model_validate_json",
        classmethod(spy),
    )
    files = slice_files(builder())

    assert calls == [files["context-model.json"]]
