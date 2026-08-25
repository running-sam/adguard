# Merged AdGuard Home Filter

Combines your 51 DNS filter lists into a single de-duplicated file
(`filters/merged.txt`) that a GitHub Action rebuilds automatically. You add
this one file as a single "DNS blocklist" in AdGuard Home instead of 51
separate ones, and it stays current on its own.

## 1. Create the repo

1. On GitHub, create a new repository (public — a private repo's raw file
   URLs need a token, which is more hassle for AdGuard Home to fetch). Any
   name is fine, e.g. `adguard-filters`.
2. Push everything in this folder to it:

   ```bash
   cd adguard-merged-filters
   git init
   git add .
   git commit -m "Initial setup"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```

Pushing `sources.txt` and `merge.py` automatically triggers the first run of
the Action (see the workflow's `push` trigger). If it doesn't fire for some
reason, trigger it by hand: on GitHub, go to **Actions → Update merged
filter list → Run workflow**.

## 2. Get the raw URL

Once the Action has run once, `filters/merged.txt` will exist in the repo.
Its raw URL is:

```
https://raw.githubusercontent.com/<your-username>/<your-repo>/main/filters/merged.txt
```

## 3. Add it to AdGuard Home

In AdGuard Home: **Filters → DNS blocklists → Add blocklist → Add a custom
list**, paste that raw URL, give it a name (e.g. "My Merged List"), and
save. AdGuard Home will periodically refetch it on its own normal refresh
schedule (configurable under Filters → DNS blocklists → the refresh
interval at the top of that page).

You can then disable or remove your 51 individual filter subscriptions in
AdGuard Home — they're now folded into this one list. (No need to rush —
having both active isn't harmful, just redundant.)

## Keeping it updated

- **The list itself**: fully automatic. The included GitHub Actions
  workflow (`.github/workflows/update.yml`) re-fetches all 51 sources and
  rebuilds `filters/merged.txt` once a day (03:17 UTC by default — edit the
  `cron` line to change that) and commits the result if anything changed.
- **Your source lists**: edit `sources.txt` (one `Name | URL` per line,
  `#` for comments), commit, and push. The push itself triggers an
  immediate rebuild, so you don't have to wait for the daily schedule.
- **Run it by hand** any time from the Actions tab → "Update merged filter
  list" → "Run workflow".

## Notes on your specific list

A few things worth knowing before you rely on this:

- **Two OISD entries**: you have both `abp.oisd.nl` (OISD Full) and
  `big.oisd.nl` (OISD Big) in your sources — these overlap heavily by
  design (Big is a superset-ish list). Keeping both just makes the merge
  bigger for very little extra blocking; consider removing one from
  `sources.txt`.
- **"Smart TV's" (`regex.list`)**: this source uses dnsmasq-style regex
  syntax rather than AdGuard/hosts syntax. It's passed through unchanged
  by the merge script, but AdGuard Home may not interpret those lines the
  way dnsmasq does. Worth testing separately, or dropping it, if you want
  to be strict about it.
- **Size**: several of your sources are large on their own (OISD Full,
  OISD Big, The Block List Project - Malware, 1Hosts Lite), so the merged,
  de-duplicated file will likely land somewhere in the hundreds of
  thousands of rules. AdGuard Home handles lists that size fine, but give
  it a moment to reload after you first add it.
- **De-duplication is exact-match only**: the script removes identical
  rule lines across lists, but doesn't try to recognize that
  `0.0.0.0 example.com` and `||example.com^` block the same domain in two
  different formats — both will be kept. That's fine for AdGuard Home (it
  understands both), it just means the "unique rules" count isn't quite
  the same as "unique domains blocked".
- **A couple of sources are best-effort**: a few URLs (e.g. the
  `urlhaus.abuse.ch` download link, the `pgl.yoyo.org` PHP endpoint) are
  dynamically generated rather than static files — they should keep
  working, but if a source ever goes offline or changes shape, the
  workflow logs a warning for that one source and still builds the merged
  file from everything else that succeeded (check the per-source
  breakdown at the top of `filters/merged.txt`, or the Action's run log).

## Files

| File | Purpose |
|---|---|
| `sources.txt` | The list of source filters (name + URL), one per line |
| `merge.py` | Fetches every source, de-dupes, writes `filters/merged.txt` |
| `filters/merged.txt` | The generated output — this is what you point AdGuard Home at |
| `.github/workflows/update.yml` | Scheduled + on-push GitHub Action that runs `merge.py` and commits the result |
| `requirements.txt` | Python dependency for `merge.py` (just `requests`) |
