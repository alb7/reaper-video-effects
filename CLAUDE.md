# Working on this repo

A collection of REAPER **Video processor** scripts (EEL2). The owner, Alberto, uses them in REAPER by pasting a script into a Video processor and saving it as a preset. He tests in REAPER; we can't run REAPER here.

## Layout

```
scripts/<name>/<name>.eel   one script per folder; file name = folder name (lowercase-kebab-case)
scripts/<name>/README.md    setup, layout/diagram, parameter table, notes, test checklist, changelog
templates/script/           what `vp.py new` copies
docs/video-processor-notes.md   API facts, runtime behaviour, gotchas, reusable patterns: read before writing EEL
tools/vp.py                 check / new / catalog (stdlib Python)
tools/test_vp.py            tests for vp.py
```

## Every change

1. Read `docs/video-processor-notes.md` before writing or editing EEL.
2. New script: `python3 tools/vp.py new <name> "<one-line description>"`, then write the script and its README.
3. Changing an existing script:
   - Bump `// @version` (patch = fix, minor = new feature or parameter, major = parameters renumbered or behaviour changed in a way that breaks saved projects).
   - Add a `### x.y.z` entry under `## Changelog` in its README.
   - Update the parameter table, diagrams and test checklist.
4. Run `python3 tools/vp.py catalog`, then `python3 tools/vp.py check` and `python3 -m unittest discover -s tools`. All must pass. CI runs the same checks.
5. When you learn something new about the Video processor (from REAPER behaviour, an error Alberto reports, or the docs), add it to `docs/video-processor-notes.md` with its source tag. If the checker could catch it, add a rule to `tools/vp.py` and a test.

## EEL2 house style

- Parenthesize every ternary used as a value, and every assignment inside a ternary branch (the checker enforces this).
- Names ignore case, so never rely on case to tell two names apart (the checker enforces this).
- Use descriptive variable names. Keep function scratch variables in `local(...)`.
- **Never renumber or remove existing `//@param` indices**: saved projects and envelopes refer to them by index. Add new parameters at the next free index. Max 40.
- Parameter names shown in REAPER should say their range or meaning, e.g. `'Transition 0=zoom 1=spring 2=slide'`.
- Snap to the end state when the transport is stopped, and after seeks (see notes, "How a script runs").
- Comment the *why* and the layout of memory arrays. Keep the header block: `@description`, `@version`, `@author`, then a few lines on how to set the script up.

## Talking to Alberto

- He edits presets in REAPER, so after a change, give him the updated `.eel` file (or point to it in the PR) and say which REAPER tests matter (the README test checklist).
- When something can't be verified without REAPER, say so plainly. If he reports a compile error, ask for the message and line number.
- Keep explanations short and concrete: layouts as small ASCII diagrams, parameters as tables.

## Git

- Work on a branch and open a PR. `main` should always pass `vp.py check`.
- Commit messages: `multiview: add 3-video layout`, `tools: check for X`, `docs: ...`.
