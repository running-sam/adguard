# Merged AdGuard Home Filter

Combines 39 DNS filter lists into a single de-duplicated file that a GitHub
Action rebuilds automatically and publishes as a GitHub Release asset
(`filters/merged.txt` is too large to commit to git, so it's published this
way instead — see "Why a Release asset" below). You add one URL as a single
"DNS blocklist" in AdGuard Home instead of dozens of separate ones, and it
stays current on its own.

## 1. Get the URL

The merged list is always available at:

```
https://github.com/running-sam/adguard/releases/download/latest/merged.txt
```

This URL never changes — the `latest` release's `merged.txt` asset is
overwritten every time the Action runs, so you only need to add it once.

## 2. Add it to AdGuard Home

In AdGuard Home: **Filters → DNS blocklists → Add blocklist → Add a custom
list**, paste that URL, give it a name (e.g. "My Merged List"), and save.
AdGuard Home will periodically refetch it on its own normal refresh
schedule (configurable under Filters → DNS blocklists → the refresh
interval at the top of that page).

## Keeping it updated

- **The list itself**: fully automatic. The included GitHub Actions
  workflow (`.github/workflows/update.yml`) re-fetches all sources and
  rebuilds `filters/merged.txt` once a day (15:17 UTC by default — edit the
  `cron` line to change that) and re-publishes it as the `latest` release
  asset.
- **Your source lists**: edit `sources.txt` (one `Name | URL` per line,
  `#` for comments), commit, and push. The push itself triggers an
  immediate rebuild, so you don't have to wait for the daily schedule.
- **Run it by hand** any time from the Actions tab → "Update merged filter
  list" → "Run workflow".

## Why a Release asset instead of committing the file

The merged file is well over 100MB, and GitHub hard-blocks any git commit
containing a file bigger than that. GitHub Releases support assets up to
2GB, so the workflow uploads `filters/merged.txt` there instead
(`gh release upload latest filters/merged.txt --clobber`) rather than
committing it — this also avoids growing the git repo by ~100MB+ on every
single daily run.

## Notes on this list

A few things worth knowing before you rely on this:

- **"Smart TV's" (`regex.list`)**: this source uses dnsmasq-style regex
  syntax rather than AdGuard/hosts syntax. It's passed through unchanged
  by the merge script, but AdGuard Home may not interpret those lines the
  way dnsmasq does. Worth testing separately, or dropping it, if you want
  to be strict about it.
- **De-duplication is exact-match only**: the script removes identical
  rule lines across lists, but doesn't try to recognize that
  `0.0.0.0 example.com` and `||example.com^` block the same domain in two
  different formats — both will be kept. That's fine for AdGuard Home (it
  understands both), it just means the "unique rules" count isn't quite
  the same as "unique domains blocked".
- **One source currently fails to fetch**: Malicious Lists #2 (digitalside
  OSINT latestdomains). The workflow tolerates single-source failures — it
  logs a warning and still builds the merged file from everything else
  that succeeded. Check the per-source breakdown at the top of
  `filters/merged.txt` (or the Action's run log) if you want to see
  current status or swap it out.
- **A couple of sources are best-effort**: a few URLs (e.g. the
  `urlhaus.abuse.ch` download link, the `pgl.yoyo.org` PHP endpoint) are
  dynamically generated rather than static files — they should keep
  working, but if a source ever changes shape, that's the first place to
  look.
- **Size**: two sources — The Block List Project - Malware and Malicious
  Lists #9 (RPiList-Malware) — together make up roughly 75% of the merged
  file's size (~2.7M and ~1M rules respectively). They're genuinely unique
  content, not duplicates, so this is a deliberate coverage-vs-size
  tradeoff rather than something to trim as "unnecessary." AdGuard Home
  handles a list this size fine, but give it a moment to reload after you
  first add it.
- **`sources.txt` has a detailed comment header** documenting which of the
  original 51 sources were trimmed (and why — mostly near-100% duplicates
  of other sources already in the list) and which look redundant by name
  but were deliberately kept because they contribute meaningfully unique
  content.

## Files

| File | Purpose |
|---|---|
| `sources.txt` | The list of source filters (name + URL), one per line |
| `merge.py` | Fetches every source, de-dupes, writes `filters/merged.txt` |
| `filters/merged.txt` | The generated output (not committed to git — published as the `latest` release's asset each run) |
| `.github/workflows/update.yml` | Scheduled + on-push GitHub Action that runs `merge.py` and publishes the result |
| `requirements.txt` | Python dependency for `merge.py` (just `requests`) |
