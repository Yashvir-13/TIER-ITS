# Sudo Commands

Commands requiring `sudo` **cannot run in agent background tasks** — the agent has no way to enter the password, and the task hangs silently until killed.

- **Never** run `sudo` commands via `run_command` in the background.
- **Always** present `sudo` commands as copy-paste blocks for the user to run in their own terminal.
- **Group** related sudo commands into a single block so the user only authenticates once (sudo caches credentials for a few minutes).
- **Explain** what each command does before asking the user to run it.
