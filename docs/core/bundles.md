# Pack bundles v1.0 (issue #130)

A consumer should never need a git checkout of this repo. It fetches one archive,
verifies it, and resolves the pack from the extracted directory.

## Build

```
bin/build-pack banking --out dist            # dist/banking-pack-<ver>.tar.gz + .MANIFEST.sha256
bin/build-pack banking --out dist --sign key.pem   # adds .sha256.sig (openssl dgst)
bin/build-pack --verify dist/banking-pack-<ver>.tar.gz
```

Version comes from the latest `<industry>-pack-*` tag (`docs/core/release.md`), so
**tag first, then build** — a bundle never invents a version.

## Determinism (why it matters here)

Same tree + same tag ⇒ byte-identical archive. Pinned in CI by
`scripts/test_bundle.py`, which builds twice and compares sha256.

How: entries sorted by path, every `mtime` fixed to `SOURCE_DATE_EPOCH`
(1980-01-01Z), `uid/gid = 0`, empty uname/gname, mode `0644`, PAX tar format,
gzip `mtime=0`. Any one of these left unset breaks reproducibility — the usual
culprits are gzip's embedded timestamp and tar's recorded mtime.

This is not aesthetics: if two builds of the same tag differ, a consumer cannot tell
a legitimate rebuild from a tampered artifact.

## Integrity chain

| Layer | What it proves | Where |
|---|---|---|
| per-file sha256 | a file inside the pack was not altered | `.MANIFEST.sha256` lines |
| `# bundle-sha256` | the *archive* was not altered or appended to | last line of the manifest |
| `.sha256.sig` | the archive came from the holder of the key | optional, openssl detached |

The bundle-sha line exists because the first version of `--verify` only checked
per-file hashes, and appending bytes to the `.tar.gz` passed verification. Caught by
the tamper test, fixed before this was closed.

## Allowlist, not trust

A bundle only accepts `.md .yaml .yml .json .txt`, refuses names matching
secret/token/credential/password/private-key, refuses files over 256 KB, and
**fails the build** on anything else rather than skipping it silently. A pack that
gains a PDF should break the build and be discussed, not quietly ship without it.

## How a consumer verifies

```
sha256sum -c <bundle>.MANIFEST.sha256 --ignore-missing   # per-file view
# or trust the recorded archive hash:
head -1 <bundle>.MANIFEST.sha256 > /dev/null              # header carries provenance
tail -1 <bundle>.MANIFEST.sha256 | cut -d' ' -f3 | xargs -I{} \
  sh -c 'test "$(sha256sum <bundle>.tar.gz | cut -d\" \" -f1)" = "{}"'
```

OpenGate's resolver (`--pack-root`, L4-14) runs the equivalent check before use; a
failed check must refuse the pack, not fall back to a stale copy.
