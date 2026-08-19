# Deterministic archive envelope version 1

Both portable formats use one canonical ZIP envelope with method `ZIP_STORED`:

```text
META-INF/manifest.json
META-INF/manifest.sha256
<declared payload entries>
```

`manifest.json` is UTF-8, NFC-normalized canonical JSON with recursively sorted
object keys, no insignificant whitespace, and a final LF. It declares the
format/schema locks, resource ceilings, transfer authorization when applicable,
and every payload entry as `{path,role,media_type,byte_count,sha256}` sorted by
normalized path. `manifest.sha256` is lowercase hex SHA-256 of the exact
manifest bytes plus LF.

The semantic digest hashes the same manifest identity core with
`semantic_digest` omitted. For `.owworkspace`, this binds the source profile,
trusted effective date, and exact target client boundary used for an embedded
transfer. Host paths and wall-clock timestamps never enter archive identity.

Every ZIP member uses timestamp `1980-01-01 00:00:00`, creator system Unix,
regular-file mode `0644`, UTF-8 name flag, no comment, no local or central extra
field, no data descriptor, and no compression. Local records are contiguous
from byte zero, followed immediately by contiguous central-directory records
and one EOCD ending at exact EOF. Prefix bytes, local-header overlays,
inter-record gaps, comments, and trailing bytes are forbidden even when they
are not represented as ZIP members.

Paths use the ASCII portable subset of NFC POSIX `/`, are relative, contain no
`.`/`..` segments, backslashes, drive/URI prefix, NUL, trailing dot/space
component, or Windows device-name component, and are unique under Unicode
case-folding. A path may not collide with another path's ancestor under
case-folding.

Verification order:

1. Parse the complete raw ZIP layout and require canonical local/central/EOCD
   agreement with no unparsed physical bytes.
2. Reject archive comments, unsupported flags/compression, duplicate or
   component-prefix/case-colliding names, unsafe paths, directories,
   symlink/reparse-like modes, unexpected controls, and resource breaches.
3. Read and hash `manifest.json`; compare `manifest.sha256`.
4. Strictly validate the manifest schema and semantic digest.
5. Require exact equality between declared and physical payload inventories.
6. Stream each payload and verify byte count, SHA-256, exact content schema,
   candidate restrictions, and cross-reference semantics.
7. For import, reauthorize transfer from caller-trusted date and destination
   boundary, extract to a unique staging directory without link following,
   validate all portable state, regenerate and validate derived outputs, then
   atomically create the destination.

Same archive identity is idempotent; a different existing destination is a
conflict and is never overwritten. Ceilings are 10,000 payload entries, 64 MiB
per entry, and 512 MiB total uncompressed. There is no decompression-ratio rule
because compressed entries are forbidden.

