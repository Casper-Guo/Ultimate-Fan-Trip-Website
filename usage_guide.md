# Publishing a New Season

How to compute and publish solutions to the [website](https://github.com/Casper-Guo/Ultimate-Fan-Trip-Website) for a new season.

Placeholders used below:
- `<league>`: `nba`, `nhl`, or `mlb`
- `<season>`: the season label used in the website URLs, e.g. `2026-2027` for NBA/NHL or `2026` for MLB

Both repos are assumed to be cloned side by side. Unless stated otherwise, invoke solver commands from the solver repo root and website commands from the website repo root.

## 1. Set up the environments

1. **Solver Python environment.** Create a virtual environment and install the solver as an editable package:
   ```bash
   python -m venv env && source env/bin/activate && pip install -e .
   ```
   The website converter imports `trip_solver`, so use this same environment for the website's Python scripts.
2. **Google Maps API key.** Create `trip_solver/data/api/google_maps/_secret.py` (gitignored) containing `KEY = "<api key>"`. The key needs Places API (New) and Routes API enabled.
3. **Ruby and Jekyll** (only needed for local previews). The `github-pages` gem needs Ruby 3.x. Ruby 4 is not supported yet.
   - **macOS:** the built-in Ruby 2.6 is too old. Install Ruby 3.3 (the version GitHub Pages builds with) and put it first on your `PATH`:
     ```bash
     brew install ruby@3.3
     echo 'export PATH="/opt/homebrew/opt/ruby@3.3/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
     ```
   - **WSL (Ubuntu):** the distro's Ruby is 3.x, which works. Install it with the build tools that native gems need, and install gems into your home folder so `bundle` doesn't need `sudo`:
     ```bash
     sudo apt update && sudo apt install -y ruby-full build-essential zlib1g-dev
     echo 'export GEM_HOME="$HOME/gems"' >> ~/.bashrc && echo 'export PATH="$HOME/gems/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
     gem install bundler
     ```

   Check that `ruby -v` reports 3.x, then install the gems in the website repo:
   ```bash
   bundle install
   ```
   If `make serve` later fails with `cannot load such file -- webrick`, run `bundle add webrick`.

## 2. Fetch the season data

```bash
python -m trip_solver.data.integration.<league>.integrate
```

- The script **overwrites** the five JSON files in `trip_solver/data/integration/<league>/`: `teams`, `venues`, `events`, `distance_matrix`, and `duration_matrix`.
- Venues outside the US, Canada, and Mexico are detected automatically from their Google Maps address and dropped, along with their games.
- If the script fails with `Unreachable venues: ...`, a non-drivable venue got through the country filter. Fix how that venue is looked up and re-run.

## 3. Check the data

Run these checks before solving.

1. **Game counts.** Each team should have the full regular-season schedule, split evenly between home and away:

   | League | Games per team |
   |---|---|
   | NHL | 84 (from 2026-27) |
   | NBA | 82, or 80 before the NBA Cup knockout games are scheduled |
   | MLB | 162 |

   Every team that comes up short should be explained by a known game outside North America, with exactly that many games missing. Also check for duplicate event IDs and for dates outside the season.
2. **Venue addresses.** Read every entry in `venues.json` and confirm that each address is the right arena in the right city. Don't rely on the country code alone: a bad lookup can resolve to a real but wrong US address and still pass the filter. This is most likely for neutral-site games.

Commit the new data to the solver repo once both checks pass.

## 4. Solve

Write the solutions straight into the website repo, so nothing has to be copied afterwards:

```bash
python -m trip_solver.solver.driver trip_solver/data/integration/<league> ../Ultimate-Fan-Trip-Website/data/<season>/<league>/solutions
```

- The first argument is the folder holding the step 2 JSON files. The second is where the solutions go. The website's `data/` folder is gitignored.
- The output has one folder per team, each containing `trip_duration.txt`, `driving_distance.txt`, and `driving_duration.txt`. Check that every team is present.

## 5. Generate the pages

1. The converter expects the step 2 input files in the parent folder of `solutions/`. Copy them there:
   ```bash
   cp trip_solver/data/integration/<league>/*.json ../Ultimate-Fan-Trip-Website/data/<season>/<league>/
   ```
2. From the website repo root, using the solver environment:
   ```bash
   python src/converter.py data/<season>/<league> docs/<season>
   ```
   The converter has some expectations about its arguments:
   - The **input** folder name becomes the league name in the page title.
   - The **output** folder name becomes the season label and the URL path, so it must be exactly `<season>`.
   - The output must be inside `docs/`, the Jekyll source folder. The converter refuses to write anywhere else.
3. Add the new season to `docs/index.md` by hand. The converter only writes the league and team pages.

## 6. Preview and publish

1. Preview locally with `make serve` in the website repo.
2. Commit the new folder under `docs/` and the `docs/index.md` change, then push to `main`. GitHub Pages rebuilds the site.
