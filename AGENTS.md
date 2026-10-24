# Working on this repository (for AI agents and contributors)

This repository publishes one Agent Skill, `skills/hand-drawn-2d-animation`, for Claude Code, Codex and other Agent Skills clients.

## Layout
- `skills/hand-drawn-2d-animation/SKILL.md`: the workflow and rules. Keep it under 500 lines; detail goes in `references/`.
- `references/`: one file per step, loaded on demand. Files over 100 lines start with a table of contents.
- `scripts/`: local, free Python tools. Standard library plus Pillow and numpy; heavier dependencies are optional and imported lazily.
- `assets/examples/`: the BOLHAO example plan and the prompt it builds. `master_prompt.py build` must reproduce `bolhao_30s_prompt.txt` exactly.
- `examples/bolhao/`: the case study, with what worked and what failed.
- `.claude-plugin/` and `.agents/plugins/`: marketplace catalogs for Claude Code and Codex.

## Rules
1. Frontmatter uses only spec fields: `name`, `description`, `license`, `compatibility`, `metadata`. The name matches the folder.
2. Prompt templates describe technique. Never add film, studio or artist names to a prompt; credits live in `references/13-credits-and-style.md` and the README.
3. No model weights, no files over 5 MB, no personal paths, no credentials. Example media must be original and small.
4. Run `python3 -m pytest -q tests` before committing. CI also greps for personal paths.
5. Change the version in one place only (`.claude-plugin/marketplace.json`, mirrored in `SKILL.md` metadata) and add a CHANGELOG entry.
6. Write plainly: short sentences, no em dashes, numbers measured rather than guessed. Mark anything not verified as such.
