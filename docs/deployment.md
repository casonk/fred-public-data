# Deployment modes: fred-public-data

fred-public-data runs three ways. You choose with one setting, and **only the `k3s` mode needs a cluster**. If you just
want to run it, you need Python and nothing else.

| Mode | What it is | Needs |
|---|---|---|
| `dev` (default) | one run in the foreground, no systemd, no cluster | the language runtime |
| `host` | the systemd user timer runs the job on the host | systemd |
| `k3s` | the same timer triggers the job, which runs in a pod; its guards and post-steps stay on the host | K3s, podman, kubectl, the in-cluster registry |

The application code is the same in all three: nothing under `src/` knows which mode it is in.

## Choose a mode

```bash
deploy/deploy.sh mode                  # print the mode in effect and where it came from
deploy/deploy.sh up                    # run it in that mode
deploy/deploy.sh status | verify | down
```

The mode is read from, first match wins:

1. `--mode dev|host|k3s` on the command line
2. `FRED_DEPLOY_MODE` in the environment
3. `FRED_DEPLOY_MODE` in `config/deploy.local.env` (copy `config/deploy.example.env`; it is gitignored)
4. `dev`

An unknown value, or a config file that cannot be read, is an error, never a silent fallback.

## What each mode does

### dev
`up` runs the job once in the foreground. `status` and `verify` check it without changing anything.

### host
`up` removes the K3s drop-in from the unit (if there) and enables the systemd user timer (install it once with
Clockwork; `up` says so if it is missing). `down` disables the timer.

### k3s
The host timer stays the trigger, so its job guard, resource-arbiter limits and any post-step keep working; only the work
moves into a pod. `up` refuses to start, and changes nothing, unless kubectl, podman, the in-cluster registry and the
host timer are present. Then it builds the image (refusing uncommitted source), applies the manifests (the CronJob is
only a **suspended template**), runs `verify.sh` (which must pass), and only then installs a systemd drop-in that
replaces the unit's `ExecStart` with `deploy/k3s/run-job.sh`. That script creates one Job from the template, streams
its log into the journal and exits with the job's status. A failed step changes nothing.

## Switching

| From | To | Command |
|---|---|---|
| dev | host | `deploy/deploy.sh --mode host up` |
| host | k3s | `deploy/deploy.sh --mode k3s up` (verifies first, then points the unit's `ExecStart` at the pod) |
| k3s | host | `deploy/deploy.sh --mode host up` (removes the drop-in; the unit runs on the host again) |

`--mode k3s down` is the same as `--mode host up`. A marker in `~/.local/state/fred-public-data/` records which mode last
held the work, so `host up` knows what to stop first.

## For contributors without K3s

- `pytest` needs no cluster: the deployment tests parse manifests and run the scripts against stub commands.
- Nothing under `deploy/k3s/` runs unless you select the `k3s` mode.
- This file, the scripts and their tests started from traction-control's `scripts/scaffold_deployment_modes.py`;
  the contract is in its `docs/deployment-modes.md`. Run `scripts/check_deployment_modes.py --repo .` to check.

## fred-public-data specifics (k3s)

The refresh runs on a host timer under the portfolio's job guard and resource limits, so k3s mode keeps that timer as
the trigger and only moves the work into a pod (see `docs/deployment-modes.md` in traction-control, "Triggered job").

- **No credentials.** The pod uses FRED's keyless public CSV endpoint. Its egress allows `fred.stlouisfed.org` only;
  `api.stlouisfed.org` is closed (it would be needed only if you set `FRED_API_KEY`, which k3s mode does not pass).
- **Data stays on the host.** `data/` and `viz/` are mounted read-write from this checkout, so notebooks and the
  host mode read the same files. `deploy/k3s/prepare-host.sh` labels them for containers; its output says how to undo it.
- **Switching.** `deploy/deploy.sh --mode k3s up` installs a drop-in that points the unit's `ExecStart` at
  `deploy/k3s/run-job.sh`; `--mode host up` removes it.
