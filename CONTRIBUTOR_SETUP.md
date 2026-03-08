# Contributor setup – SiddharthChopra branch

Follow these steps to pull the latest code and start contributing on your branch.

## 1. Make sure Git is available

- If **Git is not installed**: install [Git for Windows](https://git-scm.com/download/win), then **close and reopen** your terminal (or Cursor).
- If Git is installed but not found in this terminal: try opening **Git Bash** (from Start menu) or a new terminal after a restart.

## 2. Clone the repo (first-time setup)

Your `SikhSituationBot` folder is currently empty. In a terminal where `git` works, run:

```bash
cd c:\Users\siddh\SikhSituationBot
git clone https://github.com/gurpreethgnis/sikhsituationbot.git .
```

The `.` at the end clones into the current folder so you don’t get a nested `sikhsituationbot` folder.

## 3. Pull latest and switch to your branch

From the repo root (`c:\Users\siddh\SikhSituationBot`):

```bash
# Update main
git checkout main
git pull origin main

# Create and switch to your branch (UX role per README)
git checkout -b feature/siddharthchopra-ux
```

If the branch already exists on the remote:

```bash
git fetch origin
git checkout feature/siddharthchopra-ux
git pull origin feature/siddharthchopra-ux
```

If you prefer the branch name **SiddharthChopra** (no prefix):

```bash
git checkout -b SiddharthChopra
```

## 4. Start contributing

- **Your focus (from README):** UX – Chat flows, persona UI.
- Pick tasks from **TASK_ASSIGNMENTS.md** and work on your branch.
- Commit often with clear messages, e.g. `feat: add chat input component`.
- When ready, open a **Pull Request** from your branch to `main`.

## Quick reference

| Action              | Command |
|---------------------|--------|
| See status          | `git status` |
| See branches        | `git branch -a` |
| Pull latest on main | `git checkout main` then `git pull origin main` |
| Update your branch  | `git pull origin feature/siddharthchopra-ux` (or your branch name) |

Repo: https://github.com/gurpreethgnis/sikhsituationbot
