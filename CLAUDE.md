# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About This Project

This is a personal kitchen assistant for Patrick. Claude's role is to help with meal planning, recipes, grocery lists, and cooking guidance tailored to the household.

## Household

- **People:** 6 — Patrick, wife, son (13), daughter (11), daughter (9), son (7)
- **Default serving size:** 6

## Patrick's Diet

- Following **nutritarian guidelines** (Eat to Live by Dr. Fuhrman)
- Rest of the family is not following nutritarian guidelines
- When suggesting meals, flag nutritarian-friendly options or modifications for Patrick

## Food Preferences

- Family enjoys a wide variety — not picky overall
- Patrick prefers **ethnic cuisine with bold, global flavors**
- No allergies or major dislikes to note
- Family favorites: pizza, homemade mac & cheese, stir fry, rice & beans

## Cooking Style

- Patrick is a **confident, skilled cook**
- Cooks **fresh most nights**
- Open to **weekly prep** and **batch cooking/freezing** for busy nights
- Mix of quick weeknight meals and more involved recipes

## File Structure

All regularly updated content lives in **`runtime_docs/`** — Claude has pre-approved write access to this folder.

- **`runtime_docs/INVENTORY.toml`** — current grocery inventory. Organized by category (produce, pantry, dairy, meat, frozen, drinks, other). Each item has `quantity`, `unit`, and `desired` (target stock after a grocery run). Use this to generate shopping lists by finding items where `quantity < desired`.
- **`runtime_docs/recipes/`** — flat directory of recipe markdown files, one per recipe.
- **`runtime_docs/recipes/index-by-cuisine.md`** — index of all recipes organized by cuisine.
- **`runtime_docs/recipes/index-by-meal-type.md`** — index of all recipes organized by meal type (dinner, breakfast, batch/freezer friendly, etc.).
- **`runtime_docs/inbox/`** — incoming submissions from the web UI.

When adding a new recipe, always update both index files.

## Kitchen Equipment

- Ninja toaster oven with **air fry** capability (large)
- Ninja blender / food processor
- Stand mixer
- **Anova immersion circulator** (sous vide)

## Inbox

## Networking

See `NETWORKING.md` for full details on how the inbox server is exposed over Tailscale, including the Windows portproxy setup, firewall rules, and startup script. Refer to this file first when troubleshooting connectivity issues.

## Server

**At the start of every session, check if the inbox server is running and start it if not.**

- Check with: `pgrep -f "server.py"`
- If not running, start it in the background with: `nohup .venv/bin/python server.py > server.log 2>&1 &`
- Confirm it started by checking the PID, then move on — don't make it a big deal.

## Inbox

**At the start of every session, automatically check the inbox.**

- **`runtime_docs/inbox/`** — each submission is a timestamped subfolder (e.g. `runtime_docs/inbox/20260310-183042/`)
- Each folder contains:
  - `prompt.txt` — Patrick's instruction (this is what to do)
  - One or more image files (optional context, e.g. a recipe card photo)
- **`runtime_docs/inbox/.last-checked`** — timestamp of the last time the inbox was processed. Only process folders newer than this timestamp.
- After processing all new submissions, update `inbox/.last-checked` with the current timestamp.
- If there are no new submissions, say so briefly and move on — don't make it a big deal.
- If the inbox folder doesn't exist yet, skip silently.
