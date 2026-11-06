# REAPER Video Processor Scripts

Scripts for REAPER's **Video processor** plugin: layouts, transitions and other video effects written in EEL2.

## Scripts

<!-- catalog:start -->
| Script | What it does | Version |
|---|---|---|
| [fade-to-colour](scripts/fade-to-colour/) | Fade the video to black, to white, or to a colour you pick | 1.0.0 |
| [multiview](scripts/multiview/) | Show 1, 2, 3, 4 or 6 videos in a grid, with animated transitions between layouts | 1.3.0 |
<!-- catalog:end -->

Each script's folder has a README with its parameters, layouts and changelog.

## Using a script in REAPER

1. On the track (or item) where you want the effect, add the FX **Video processor**.
2. Open its code editor, select all, and paste in the contents of the script's `.eel` file.
3. Save it as a preset from the FX window's preset menu, so you can add it to other projects in one click.
4. Adjust the knobs, or right-click a knob and add an envelope to automate it.

Most scripts that combine several videos (like `multiview`) go on a track **below** the tracks with the video sources.

## Repository layout

```
scripts/<name>/      one folder per script: <name>.eel + README.md
templates/script/    starting point for new scripts
docs/                notes on the Video processor API and its gotchas
tools/vp.py          checks scripts, scaffolds new ones, updates the table above
```

## Developing

```sh
python3 tools/vp.py new my-effect "What it does"   # scaffold a new script
python3 tools/vp.py check                          # lint everything (also runs in CI)
python3 tools/vp.py catalog                        # refresh the table above
```

`vp.py check` catches the EEL2 mistakes that are easy to make and hard to see: unparenthesized ternaries, variable names that differ only in case (EEL2 ignores case), unbalanced parentheses, and bad `//@param` lines. It also checks that each script's version has a changelog entry.

### Working with Claude

`CLAUDE.md` tells Claude how this repo works, so you can ask for a new script or a change in any Claude Code session that has the repo connected. If the Claude GitHub workflow is set up (see `.github/workflows/claude.yml`), you can also open an issue or comment on one with `@claude` and a request, and Claude replies with a pull request.

## License

MIT, see [LICENSE](LICENSE).
