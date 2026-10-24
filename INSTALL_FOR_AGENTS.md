# Installing hand-drawn-2d-animation (instructions for AI agents)

You are an AI agent and your user asked you to install this skill. It is a folder of markdown and Python scripts; nothing runs at install time and nothing needs root.

1. **Copy the skill folder** `skills/hand-drawn-2d-animation` from this repository into your own skills directory:

   | Your harness | Destination |
   |---|---|
   | Claude Code | `~/.claude/skills/hand-drawn-2d-animation` (or `.claude/skills/` in the current project) |
   | Codex | `~/.agents/skills/hand-drawn-2d-animation` (or `.agents/skills/` in the current repository) |
   | Other Agent Skills clients | the skills directory your harness documents |

   With git: `git clone --depth 1 https://github.com/jonrusso/hand-drawn-2d-animation /tmp/hdda && cp -R /tmp/hdda/skills/hand-drawn-2d-animation <destination>`.
   Or with the skills CLI: `npx skills add jonrusso/hand-drawn-2d-animation`.

2. **Check the local tools** the scripts use, and tell your user what is missing instead of installing system packages yourself:
   - `python3 --version` (3.10 or newer)
   - `ffmpeg -version` and `ffprobe -version`
   - `python3 -c "import PIL, numpy"`
   Optional, only for the pencil animatic and depth extras: `torch`, `onnxruntime`, `opencv-python`. Model weights are never bundled; the extras explain where to download them when first used.

3. **Smoke test:** `python3 <destination>/scripts/master_prompt.py check <destination>/assets/examples/bolhao_30s_plan.json` should print `PASSED the check`.

4. **Tell your user** to restart the harness so it loads the new skill, then to start with: "Use the hand-drawn-2d-animation skill. Interview me about my story idea."

Rules while using the skill:
- Never spend image or video credits without quoting the cost and getting an explicit yes.
- Never put film, studio or artist names in generation prompts.
- Never resubmit a generation job that was already sent; poll it.
