# buzz-collector

Always-on ApeWisdom mention collector for `buzz_screener.py`. GitHub Actions
pulls the leaderboard twice a day and commits one CSV per UTC day to
`data/mentions/`. The screener merges those files into its local SQLite at
the start of every run (`sync_from_github`), so the baseline no longer has
holes when the desktop is asleep. The desktop keeps collecting too; the
two are unioned (max mentions per ticker per day), never overwritten.

## One-time setup (5 minutes)

1. Create a new GitHub repository (private is fine), e.g. `buzz-collector`.
2. Copy this folder's contents into it, then seed it with the history you
   already have:

       python export_history.py "C:\Users\maide\buzz_screener\buzz_history.db"

3. Commit and push everything (`git add -A && git commit -m "seed" && git push`).
4. In the repo on github.com: **Actions** tab -> enable workflows if asked ->
   open **collect-mentions** -> **Run workflow** once to confirm it commits.
5. In `buzz_screener.py` set `"HISTORY_REPO": "<your-user>/buzz-collector"`.
   If the repo is private, create a fine-grained personal access token with
   *Contents: Read* on that repo and `setx GITHUB_TOKEN "<token>"` (new shell
   afterwards). Public repo: no token needed.
6. Run `python buzz_screener.py --collect-only` on the desktop; the `[sync]`
   line should report the day-files merged.

## Notes

- Scheduled workflows are paused by GitHub after 60 days with no repo
  activity; the collector's own commits count as activity, so this never
  triggers while it is working. If it ever stops, the Actions tab shows why.
- Each run takes ~20 s of Actions minutes; the free tier allows ~2,000/month.
- `data/mentions/*.csv` is the durable record. `buzz_history.db` on the
  desktop is a derived union of these files plus local pulls.
