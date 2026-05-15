# Refresh

Release-aware refresh jobs.

Current MVP:

- `ingest_releases.py` reads `knowledge/release_source_registry.json`
- fetches official OCI release pages when network access is available
- falls back to seeded release text for offline development
- classifies release items by service, domain, impact tags, and impact level
- writes `knowledge/snapshots/oci-release-snapshot.json`
- `refresh_policy.py` compares release snapshots, maps new important items to affected knowledge sources, selectively refreshes only those chunks, and runs post-refresh gates

Run from the repository root:

```bash
python3 knowledge/refresh/ingest_releases.py
```

Offline fallback mode:

```bash
python3 knowledge/refresh/ingest_releases.py --no-fetch
```

Run the policy workflow:

```bash
python3 knowledge/refresh/refresh_policy.py --mode release-watch
```

Quick local smoke:

```bash
python3 knowledge/refresh/refresh_policy.py --mode release-watch --no-fetch --quick-gates
```

Future jobs should generate richer architecture-impact deltas and publish refresh health into OCI Monitoring.
