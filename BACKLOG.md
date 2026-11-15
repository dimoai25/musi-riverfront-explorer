# Backlog

The working list for the Musi Riverfront Explorer. This repo is public, so keep personal and business plans out of this file.

Tick an item when it ships, and add a line on what changed.

## Next

- [ ] **"What's new" strip.**
  - One short line at the top of the explorer with the latest change (for example "Zone 1A tender documents added").
  - Tapping it opens a short dated changelog of explorer updates only. No project timelines, per the guardrails.
- [ ] **Updates sign-up, with no group to run.**
  - One-way only: an email form (Buttondown, a Google Form or similar) or "Follow on X for updates". No WhatsApp group or community to moderate.
  - Ask only for an email address. Say what it's for and how to unsubscribe.
  - Count sign-ups as a PostHog event.
- [ ] **UI/UX pass.** Collect the specific items here as they come up. Known so far:
  - On phones, the left swipe label ("Today" / "Satellite") hides under the mode badge.
  - Check how the amber disclaimer reads in dark mode.
  - **"Map layers" panel has no visible close control.**
    - Once it's open, the only way to close it is tapping the card's header, top right, and nothing shows that.
    - Fix: give the header an obvious close button (an × or "Hide", at least 44 px to tap) and a chevron that turns when open.
    - On phones, also close it when the map is tapped.

## When something changes in the project

Update the explorer only when one of these happens:

- [ ] **Zone 1A tender documents** (contract 06/CE/MRDCL/2026-27).
  - Review them together.
  - Add the sources per stretch, and any stops or features they support.
- [ ] **Agriculture Research Institute stretch:** waiting on the owner's follow-up. Leave it out until there is a reliable source.
- [ ] **Tender award or a new drawing revision** (after Rev R02).
  - Update the drawings, `SOURCES` and the "What's new" line.
  - Rebuild tiles with `sh tools/make_xyz.sh`.
- [ ] **Construction visible on satellite:** a before/after view once the imagery shows work on site.

## Analytics

- [ ] **Owner:** add the `POSTHOG_KEY` repo secret (and the `POSTHOG_HOST` variable if the account is on EU), then run the deploy workflow.
- [ ] **Check that `$pageleave` arrives.** It is sent with `sendBeacon` as `text/plain` when the page closes. If PostHog drops it, switch it to a keepalive `fetch` with JSON.
- [ ] **Starter insights in PostHog:**
  - `stop_viewed` broken down by `stop`
  - `base_map` = sat
  - visits by `utm_source`
  - a funnel from `$pageview` → `stop_viewed` → `link_clicked`
- [ ] Use tagged links in posts (`?utm_source=x&utm_campaign=…`, `?utm_source=whatsapp`).

## Later

- [ ] **"Made by" line:** a quiet credit linking to the owner's X profile ("independent analysis, no builder ties"). No sales pitch on the map.
- [ ] **Location context:** "What's planned within 1 km of here" as a general area view. It must not read as an impact judgement on any one property; check it against the guardrails first.
- [ ] **Monthly post from analytics:** the most-explored stretch and stops, aggregate counts only.
- [ ] **Refresh the share image** (`site/og.png`) with a satellite + plan view.
- [ ] **Platform ideas parked in the earlier Wayfinder plan:** buyer access (WF-02), a 3D prototype (WF-09), and a download task (WF-11).

## Tech debt

- [ ] **GitHub Actions on Node 20 is deprecated.** Bump `actions/checkout`, `configure-pages`, `upload-pages-artifact` and `deploy-pages` once Node 24 versions are out.
- [ ] **The v2 tile bundles in `site/tiles/` (about 30 MB) are still deployed**, though the MapLibre page only uses them as the warp source. Move them out of `site/` (for example to `data/raster/`), point `tools/make_xyz.sh` at the new path, and the deploy shrinks by half.
- [ ] **Alignment:** RMS 13 m, worst at cp7 (the Narsingi roundabout, 26 m).
  - Add two or three control points in the south of Zone 1A, where there are few today.
  - Refit and recheck the leave-one-out errors.
- [ ] **Dead build output:** `tools/build_v2_page.py` still writes the old claude.ai artifact version. Drop that output.
- [ ] **ArcGIS key expiry:** the key lasts one year from creation (Nov 2026). Regenerate it before it expires and update the `ARCGIS_KEY` secret. Satellite switches off quietly if it lapses.
