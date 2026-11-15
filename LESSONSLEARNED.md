# LESSONSLEARNED.md

Tracked durable lessons for `fred-public-data`.
Unlike `CHATHISTORY.md`, this file should keep only reusable lessons that should change how future sessions work in this repo.

## How To Use

- Read this file after `AGENTS.md` and before `CHATHISTORY.md` when resuming work.
- Add lessons that generalize beyond a single session.
- Keep entries concise and action-oriented.
- Do not use this file for transient status updates or full session logs.

## Lessons

- Document the repository around its real execution, curation, or integration flow instead of only the top-level folder list.
- Keep local-only, private, reference-only, or generated boundaries explicit so published or runtime behavior is not confused with offline material or non-committable inputs.
- Re-run repo-appropriate validation after changing generated artifacts, diagrams, workflows, or other CI-facing files so formatting and compatibility issues are caught before push.
- Data-mirror repos still need the shared portfolio starter governance and architecture files; missing baseline docs can break portfolio audit jobs even when the runtime code itself is healthy.

### 2026-11-15 — A refresh nobody scheduled

- An empty `data/` was the only sign that nothing ever ran the refresh: there was no timer. A repository that
  documents a recurring job should ship its Clockwork manifest, and a check that its data folder is not empty.
- The public CSV endpoint needs no key; keep the pod's egress to that one host and leave the API host closed unless a
  key is configured.
- New top-level folders (`deploy/`, `config/`) break `pip install -e .` here too without `py-modules = []`.
