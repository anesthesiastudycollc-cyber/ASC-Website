# ASC TikTok autopilot

Account: @anesthesiastudyco (TikTok Business) · Metricool brand 6389044 · timezone America/New_York.
Goal: get anesthesia students (AA/CAA, SRNA/CRNA), trainees and early-career providers to follow and come back daily.
Clinical accuracy, book map and website rules: see PLAYBOOK.md (they apply here too).

## Daily slots
| Slot | Format | What |
| --- | --- | --- |
| 12:30 PM | `brand` | Company spotlight. Always the first post of the day. |
| 8:30 PM | `case` | Educational Quick Case. |
After 2+ weeks of TikTok data, move both slots to getBestTimeToPostByNetwork (tiktok) times: company post first, slots at least 5 hours apart. Record any change here.

## Brand kit
- Faceless only: animated graphics, monitors and drawn product mockups. No people, faces, hands-on-camera or AI imagery.
- Never name the owner, a university, a professor or an exam (gen_tiktok.py refuses specs that do).
- Colors: navy background (#08122A to #102452) with grid + EKG motif, light blue #82CDF5, cyan #00BCD4, white cards, yellow #FFD600 highlights, red #F04848 alarms, monitor green #00E676.
- Font: Montserrat (ExtraBold headlines, Bold/SemiBold body) from _src/fonts.
- Logo: drop a transparent PNG at `_src/brand/logo.png` and it is used in the header and outro automatically. Without it a white EKG badge is drawn.
- Footer: "© <year> Anesthesia Study Co. LLC" (+ "Teaching reference, not a medical directive." on cases).
- Sound: soft synthesized cues only (monitor beeps, countdown ticks, reveal chime). TikTok's API can't attach trending sounds.

## Layout and safe zone (1080 x 1920)
- Keep all content in x 64-936, y 230-1440. TikTok covers the top ~150 px (tabs), the right rail x > 940 (y 600-1500) and the bottom ~430 px (caption, sound).
- gen_tiktok.py shrinks text to fit and raises an error instead of clipping. If a render fails with "does not fit" or "too long", shorten that field.
- The contact sheet (`<outdir>/contact.jpg`) shades TikTok's UI zones in red. Check every frame: nothing important under red, no overlaps.

## Timelines and contact-sheet frames
- brand (16 s): hook + mockup 0-2.2 · kicker 2.2-4.0 · points 1/2/3 in at 4.0/6.6/9.2 · where-to-get-it 11.6-13.4 · outro 13.4-16. Frames 1.5, 2.9, 7.8, 10.5, 12.2, 14.5 s.
- case (22 s): monitor + scene 0-3.2 (live ECG, blinking alarms) · question + options 3.2-6.2 · 3-2-1 countdown 6.2-9.2 · reveal 9.2-12.2 · why 12.2-17.2 · pearl + CTA 17.2-22.2. Frames 2, 4.5, 8, 10.5, 14, 20 s.

## Weekday rotation (12:30 brand posts)
| Day | Product | mockup.type | Where line (examples) |
| --- | --- | --- | --- |
| Mon | Meet ASC (who we are, what we make, who it's for) | `meet` | Books on Amazon · mind maps at anesthesiastudyco.com |
| Tue | Clinical logbooks and case trackers | `logbook` | On Amazon: search Anesthesia Study Co. |
| Wed | Mind maps | `mindmap` | $5 each at anesthesiastudyco.com |
| Thu | Study guides | `guide` | Study guides on Etsy: AnesthesiaStudyCo |
| Fri | Medication study cards (and coloring study books) | `cards` | On Amazon: search Anesthesia Study Co. |
| Sat | On Amazon (books, quick charts, planner) | `books` | Anesthesia Study Co. author store on Amazon |
| Sun | BLS + ACLS training / the website | `bls` or `web` | anesthesiastudyco.com |
Each week: a fresh hook, kicker, 3 points and outro. Show what's inside, who it's for and how it helps on a clinical day, not just "buy". App: "coming soon" only, never a date.

## Spec fields
Specs are JSON lists: `_src/tiktokN-am.json` (7 brand) and `_src/tiktokN-pm.json` (7 case). Example: `tiktok-sample.json`.

brand:
- `date` YYYY-MM-DD · `format` "brand" · `slot` "12:30" · `product` (rotation name)
- `label` header tag (default SPOTLIGHT) · `chip` small yellow tag above the hook
- `hook` ≤ ~12 words · `kicker` one sentence · `points_title` (default WHAT'S INSIDE) · `points` exactly 3, ≤ ~10 words each
- `mockup` {`type`: meet | logbook | mindmap | guide | cards | books | bls | web, `title`, `labels` [...]}
- `where` where to get it · `outro` short brand line · `tagline` small line under the follow pill · `caption`

case:
- `date` · `format` "case" · `slot` "20:30" · `topic` (for the log) · `series` optional chip ("Day 2 of Airway Week", "Would you extubate?")
- `vitals` up to 4 {`label`, `value`, `alarm`: true on abnormal values}
- `scene` ≤ ~25 words · `question` short · `options` exactly 4, ≤ ~6 words each · `correct` "A"-"D"
- `why` ≤ 40 words · `pearl` ≤ 14 words · `cta` (e.g. "Comment your pick") · `caption`

## Caption rules (checked by gen_tiktok.py)
1. First line: scroll-stopping hook, under 100 characters.
2. 1-3 short lines.
3. CTA: comment your pick / save / follow @anesthesiastudyco.
4. Exactly: `📚 More: Anesthesia Study Co. on Amazon + anesthesiastudyco.com (link in bio)`
5. 4-6 hashtags from #anesthesia #anesthesiastudent #crna #srna #caa #anesthesiastudyco, swapping in topic tags.
No patient identifiers.

## Publishing (Metricool)
blogId 6389044 · providers [{"network":"tiktok"}] · autoPublish true · draft false · 12:30 or 20:30 America/New_York.
tiktokData: privacyOption PUBLIC_TO_EVERYONE · disableComment/disableDuet/disableStitch false · isAigc false · commercialContentOwnBrand true (brand) / false (case).
Media: https://cdn.jsdelivr.net/gh/anesthesiastudycollc-cyber/ASC-Website@<hash>/tiktok/<am|pm>/<date>/reel.mp4, videoThumbnailUrl .../cover.jpg.

## Topic log (no repeats within 8 weeks)
Instagram topics older than 2 weeks may be re-cut with a new hook and scene. Log every TikTok case topic and brand angle here.
| Date | Slot | Topic / angle |
| --- | --- | --- |
