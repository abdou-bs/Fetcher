<p align="center">
  <img src="https://img.icons8.com/fluency/96/calendar.png" alt="Fetcher Logo" width="96" />
</p>

<h1 align="center">Fetcher — UVSQ CELCAT Calendar</h1>

<p align="center">
  <strong>Auto-updating university calendar you can subscribe to — 100% free, no server needed.</strong>
</p>

<p align="center">
  <a href="https://github.com/AbdelkarimDouadjia/Fetcher/actions/workflows/update-calendar.yml">
    <img src="https://github.com/AbdelkarimDouadjia/Fetcher/actions/workflows/update-calendar.yml/badge.svg" alt="Update Calendar" />
  </a>
  <img src="https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License" />
  <img src="https://img.shields.io/badge/CELCAT-UVSQ-purple" alt="CELCAT UVSQ" />
</p>

---

## What is this?

**Fetcher** scrapes the [CELCAT UVSQ](https://edt.uvsq.fr) timetable, filters only **your** modules and TD groups, and generates a clean `.ics` calendar file that you can subscribe to from **Google Calendar, iPhone, Outlook, or any calendar app**.

A GitHub Actions cron job **automatically refreshes** the calendar every 6 hours — so when a class is moved, a room changes, or a session is cancelled, your calendar updates by itself. No server, no hosting costs, **just GitHub**.

### What you get

| Feature | Description |
|---|---|
| **Auto-update** | Calendar refreshes every 6 hours via GitHub Actions |
| **Smart filtering** | Only your enrolled modules + your TD/TP group |
| **Exam detection** | Exams, midterms, and defenses always included |
| **Room & location** | Full room info (e.g. `AMPHI B - DESCARTES`, `G207 - GERMAIN`) |
| **Reminders** | Built-in 30 min + 1 day before alarms |
| **Stable UIDs** | Events update in-place — no duplicates |
| **100% free** | GitHub Actions + GitHub Pages, no paid service |

---

## Two Ways to Use This

### Option A — Quick Download (no GitHub account needed)

Visit the **online tool** at:

```
https://abdelkarimdouadjia.github.io/Fetcher/
```

1. Pick your modules and TD group
2. Click **"Generate & download .ics"**
3. Import the file into your calendar app

> This gives you a one-time `.ics` file. To get **automatic updates** every 6 hours, use Option B.

---

### Option B — Auto-updating Calendar (recommended, needs free GitHub account)

This creates your own personal calendar URL that **refreshes every 6 hours** automatically.

> **⚠️ Important:** Downloading or cloning the repo on your computer is **not enough**. The project must live in a repository on **your own GitHub account** for GitHub Pages and GitHub Actions to work.

#### Step 1 — Create your own GitHub copy

1. [**Sign up for a free GitHub account**](https://github.com/signup) if you don't have one
2. Go to [**this repository**](https://github.com/AbdelkarimDouadjia/Fetcher)
3. Recommended: create a **normal repository on your account** with these files
4. If the repo owner enables **Use this template**, use that button
5. If not, create a new public repo on your account and upload or push this project into it
6. A **fork** also works, but GitHub disables workflows on forks by default

Your copy will be at `https://github.com/<your-username>/<repo-name>`

> **Tip:** If you keep the repo name as `Fetcher`, all the example URLs below work exactly as written. If you rename it, replace `Fetcher` with your repo name.

#### Step 2 — Edit your modules

1. In **your GitHub copy**, click the file `calendar-config.json`
2. Click the **pencil icon** ✏️ (top-right of the file) to edit it directly on GitHub
3. Replace the modules with **your own** from your [contrat d'études](https://inscription.uvsq.fr/ipweb/jsp/contrat_peda_standalone.jsf):

```json
{
  "startDate": "2026-01-19",
  "endDate": "2026-08-31",
  "modules": [
    { "code": "MIN17212", "name": "Simulation", "tdGroup": 1 },
    { "code": "MSANGS2I", "name": "Anglais", "tdGroup": 4 },
    { "code": "MIN17214", "name": "Conception de BD", "tdGroup": 2 }
  ]
}
```

4. Click **"Commit changes"** (the green button)

**How to find your info:**

| Field | Where to find it |
|---|---|
| `code` | Module code from your [contrat d'études](https://inscription.uvsq.fr/ipweb/jsp/contrat_peda_standalone.jsf) (e.g. `MIN17212`) |
| `name` | Module name (e.g. `Simulation`) |
| `tdGroup` | Your TD group number — check your contrat or CELCAT (e.g. `TD01` → `1`) |
| `startDate` | First day of your semester (`YYYY-MM-DD`) |
| `endDate` | Last day you want covered (`YYYY-MM-DD`) |

> **Tip:** Module codes follow the pattern `MINxxxxx` or `MSANGSxx`.

#### Step 3 — Enable GitHub Pages

1. In your GitHub copy, go to **Settings** → **Pages** (left sidebar)
2. Under **Source**, select: **main** branch, **`/ (root)`** folder
3. Click **Save**
4. Wait ~1 minute — your page will be live at `https://<your-username>.github.io/<repo-name>/`

> This repo now includes `.nojekyll`, which helps GitHub Pages publish the static site directly even if Actions on a fork are still disabled.

#### Step 4 — Enable GitHub Actions

> In a normal repository, Actions is usually already enabled. On **forks**, workflows are **disabled by default**, so you must enable them manually.

1. If you used a fork, go to the **Actions** tab in your fork
2. You'll see a yellow banner: _"Workflows aren't being run on this forked repository"_
3. Click **"I understand my workflows, go ahead and enable them"**
4. Then go to **Settings** → **Actions** → **General**
5. Select **"Allow all actions and reusable workflows"**
6. Click **Save**

#### Step 5 — Run the workflow (first time)

1. Go to the **Actions** tab
2. Click **"Update Calendar"** on the left
3. Click **"Run workflow"** → **"Run workflow"**
4. Wait for the green ✓ (takes ~30 seconds)
5. Also run **"Fetch CELCAT Events Data"** the same way (this powers the online tool)

#### Step 6 — Subscribe to your calendar

Your personal calendar URL is:

```
https://<your-username>.github.io/<repo-name>/calendar.ics
```

Replace `<your-username>` with your GitHub username and `<repo-name>` with your repository name.

**Add it to your calendar app:**

| App | How to subscribe |
|---|---|
| **Google Calendar** | Other calendars **(+)** → **From URL** → paste the link |
| **iPhone / iPad** | **Settings** → **Calendar** → **Accounts** → **Add** → **Other** → **Subscribed Calendars** → paste |
| **Outlook** | **Add calendar** → **Subscribe from web** → paste the link |
| **Samsung / Android** | Open the URL in your browser → it offers to add to Calendar |

> Your calendar app will auto-refresh every 12–24 hours. GitHub Actions refreshes the data every 6 hours.

#### That's it! 🎉

From now on, your calendar stays in sync automatically. When a class is moved, a room changes, or a session is cancelled — your phone/laptop calendar updates by itself.

---

## How It Works

```
┌─────────────────┐     every 6h      ┌──────────────┐
│  GitHub Actions  │ ───────────────► │  CELCAT UVSQ  │
│  (cron job)      │ ◄─────────────── │  edt.uvsq.fr  │
│                  │   raw events      │               │
└────────┬────────┘                   └───────────────┘
         │
         │ filter by your modules
         │ + TD groups + exams
         ▼
┌─────────────────┐     git push      ┌──────────────┐
│  generate.py     │ ───────────────► │  GitHub Pages  │
│  → calendar.ics  │                  │  (static host) │
└─────────────────┘                   └───────┬───────┘
                                              │
                             https://...github.io/<repo-name>/calendar.ics
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │  Your Calendar    │
                                    │  (Google/iPhone/  │
                                    │   Outlook/etc.)   │
                                    └──────────────────┘
```

1. **GitHub Actions** runs `generate.py` every 6 hours (or on manual trigger)
2. `generate.py` reads your `calendar-config.json`, connects to CELCAT, fetches all events
3. Events are filtered: only your modules, your TD group, plus all exams
4. A fresh `calendar.ics` is generated and committed back to the repo
5. **GitHub Pages** serves it as a public URL
6. Your calendar app fetches the URL periodically and stays up to date

---

## Project Structure

```
Fetcher/
├── .nojekyll               ← Lets GitHub Pages deploy static files directly
├── calendar-config.json    ← YOUR config (modules, groups, dates)
├── calendar.ics            ← Generated calendar (auto-updated)
├── celcat-data.json        ← Pre-fetched CELCAT events (auto-updated)
├── generate.py             ← Standalone generator script
├── fetch_all_events.py     ← Fetches all events for client-side tool
├── requirements.txt        ← Python dependencies
├── index.html              ← Online tool (GitHub Pages)
├── app.js                  ← Client-side tool logic
├── style.css               ← Web app styles
├── docs.html               ← Setup & documentation guide
├── .github/
│   └── workflows/
│       ├── update-calendar.yml   ← Cron: update your calendar.ics
│       └── fetch-events.yml      ← Cron: update celcat-data.json
├── web/                    ← Flask web app (optional, for local use)
│   ├── app.py
│   ├── celcat_client.py
│   ├── event_filter.py
│   ├── ics_generator.py
│   ├── static/
│   │   ├── app.js
│   │   └── style.css
│   └── templates/
│       ├── index.html
│       └── guide.html
├── celcat_client.py        ← CLI version
├── config.py               ← CLI config
├── event_filter.py         ← CLI filter
├── ics_generator.py        ← CLI generator
└── main.py                 ← CLI entry point
```

---

## Updating Your Config

When a new semester starts or your enrollment changes:

1. Edit `calendar-config.json` (directly on GitHub: click the file → pencil icon ✏️ → edit → commit)
2. Update `startDate`, `endDate`, and your `modules` list
3. The next workflow run (within 6 hours) will pick up your changes
4. Or trigger it manually: **Actions** → **Update Calendar** → **Run workflow**

---

## Local Usage (Optional)

### CLI tool

```bash
pip install requests beautifulsoup4
python main.py
```

This reads `config.py` and generates `my_calendar.ics` locally.

### Flask web app

```bash
cd web
pip install -r requirements.txt
python -m flask run --port 5000
```

Open `http://localhost:5000` — a visual interface where you can pick modules, generate, subscribe, or update an existing `.ics`.

### Generate script (same as GitHub Actions)

```bash
pip install requests beautifulsoup4
python generate.py
```

Reads `calendar-config.json` and writes `calendar.ics`.

---

## FAQ

<details>
<summary><strong>Can I use this for a different programme (not M1 AMIS)?</strong></summary>

Currently the search term `"M1 AMIS"` is hardcoded. You'd need to edit `generate.py` and `web/app.py` to change the `search_groups()` call. PRs welcome!
</details>

<details>
<summary><strong>How often does my calendar update?</strong></summary>

- **GitHub Actions** runs every 6 hours and pushes a new `calendar.ics`
- **Your calendar app** (Google, iPhone, etc.) re-fetches the subscription URL every 12–24 hours
- So in the worst case, changes appear within ~30 hours
</details>

<details>
<summary><strong>Will I get duplicate events?</strong></summary>

No. Each event has a stable UID based on the CELCAT event ID. When your calendar app fetches the updated file, it replaces existing events — no duplicates.
</details>

<details>
<summary><strong>Can I share my calendar URL with classmates?</strong></summary>

Only if they have the **exact same** modules and TD groups. Otherwise, they should create **their own GitHub copy** of the project and set up their own config — it takes 5 minutes. Share this guide with them!
</details>

<details>
<summary><strong>My friend downloaded/cloned the repo but workflows don't run</strong></summary>

Downloading or cloning is **not enough**. They need the project in a repository on **their own GitHub account**. Best option: create a new repo with these files (or use **Use this template** if available). A fork also works, but needs extra Actions setup. See [Option B](#option-b--auto-updating-calendar-recommended-needs-free-github-account) above.
</details>

<details>
<summary><strong>I forked but Actions are disabled / not running</strong></summary>

GitHub disables workflows by default on forks. Go to the **Actions** tab and click **"I understand my workflows, go ahead and enable them"**. Then go to **Settings → Actions → General** and allow all actions.
</details>

<details>
<summary><strong>What is the easiest setup for classmates?</strong></summary>

If possible, ask them to create a **normal repo on their own account** from this project instead of forking. That avoids the extra fork workflow restrictions. If you later mark this repo as a **template repository** in GitHub settings, they can use **Use this template** directly.
</details>

<details>
<summary><strong>The workflow failed — what do I do?</strong></summary>

Usually it's a temporary CELCAT server issue. Go to **Actions** and re-run the failed workflow. If it keeps failing, check that your module codes are correct in `calendar-config.json`.
</details>

<details>
<summary><strong>Is this free?</strong></summary>

Yes, 100% free. GitHub Actions gives unlimited minutes for public repos, and GitHub Pages is free static hosting.
</details>

---

## Contributing

Found a bug? Want to add support for other programmes? PRs are welcome!

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT — free to use, modify, and distribute.

---

<p align="center">
  Made with ☕ for UVSQ M1 Info students<br/>
  <sub>Not affiliated with UVSQ or CELCAT.</sub>
</p>
