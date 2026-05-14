# Refresh

Release-aware refresh jobs.

Current MVP:

- `ingest_releases.py` reads `knowledge/release_source_registry.json`
- fetches official OCI release pages when network access is available
- falls back to seeded release text for offline development
- classifies release items by service, domain, impact tags, and impact level
- writes `knowledge/snapshots/oci-release-snapshot.json`

Run from the repository root:

```bash
python3 knowledge/refresh/ingest_releases.py
```

Offline fallback mode:

```bash
python3 knowledge/refresh/ingest_releases.py --no-fetch
```

Future jobs should compare release snapshots over time, trigger evals when knowledge changes, and generate architecture-impact deltas.
