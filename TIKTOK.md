# ASC TikTok autopilot

Account: @anesthesia.study.c (TikTok Business; Instagram is @anesthesiastudyco) · Metricool brand 6389044 · timezone America/New_York.
Goal: get the word out about ASC to anesthesia students (AA/CAA, SRNA/CRNA), trainees and early-career providers, and send every viewer to www.anesthesiastudyco.com (WEBSITE FIRST, Andrea Nov 26). Never Amazon or Etsy.
Clinical accuracy, book map and website rules: see PLAYBOOK.md (they apply here too).

## Weekly plan (2 posts/day, 14/week)
| Slot | What |
| --- | --- |
| 12:30 PM | Education: mostly Quick Case reels (`case`), a few pearl carousels (`carousel`, TikTok photo post). |
| 8:30 PM | 4 days a week: "What ASC offers" spotlight (`brand` reel or `carousel`), on different days. Other days: another Quick Case. |
- 10 education + 4 spotlights per week. Never two posts in one slot. Leave the 9:00 AM carousel posts alone and avoid their topics that week.
- Instagram topics older than 2 weeks may be re-cut for TikTok with a new hook (not a copy).
- After 2+ weeks of TikTok data, move both slots to getBestTimeToPostByNetwork (tiktok) times: at least 5 hours apart and away from 9:00 AM. Record any change here.
- Spotlight rotation: who ASC is / mission · Student Success Planner + coloring study books · clinical logbooks + case trackers · Quick Charts + quick-reference OR tools · mind maps ($5 each) · board-review resources · the website itself. Show what's inside, who it's for and how it helps on a clinical day. App: "coming soon" only, never a date.

## Generator
`python3 -I _src/gen_tiktok.py tiktokN-am.json <work>/tiktok-am` (and the pm spec). Formats: `case` and `brand` reels (1080x1920, TikTok safe zones) and `carousel` (1080x1350 slides drawn by gen.py, same slide fields as weekN.json). Writes `<date>/reel.mp4 + cover.jpg` or `<date>/slideN.jpg`, and `contact.jpg`. Every reel frame and every slide prints www.anesthesiastudyco.com. The checker rejects Amazon/Etsy, launch dates, banned names, bad caption shape.

## Brand kit
- Faceless only: animated graphics, monitors and drawn product mockups. No people, faces, hands-on-camera or AI imagery.
- Never name the owner, a university, a professor or an exam (gen_tiktok.py refuses specs that do).
- Colors: navy background (#08122A to #102452) with grid + EKG motif, light blue #82CDF5, cyan #00BCD4, white cards, yellow #FFD600 highlights, red #F04848 alarms, monitor green #00E676.
- Font: Montserrat (ExtraBold headlines, Bold/SemiBold body) from _src/fonts.
- Logo: drop a transparent PNG at `_src/brand/logo.png` and it is used in the header and outro automatically. Without it a white EKG badge is drawn.
- Footer: www.anesthesiastudyco.com (yellow, every frame) over "© <year> Anesthesia Study Co. LLC" (+ "Teaching reference, not a medical directive." on cases).
- Sound: soft synthesized cues only (monitor beeps, countdown ticks, reveal chime). TikTok's API can't attach trending sounds.

## Layout and safe zone (1080 x 1920)
- Keep all content in x 64-936, y 230-1440. TikTok covers the top ~150 px (tabs), the right rail x > 940 (y 600-1500) and the bottom ~430 px (caption, sound).
- gen_tiktok.py shrinks text to fit and raises an error instead of clipping. If a render fails with "does not fit" or "too long", shorten that field.
- The contact sheet (`<outdir>/contact.jpg`) shades TikTok's UI zones in red. Check every frame: nothing important under red, no overlaps.

## Timelines and contact-sheet frames
- brand (16 s): hook + mockup 0-2.2 · kicker 2.2-4.0 · points 1/2/3 in at 4.0/6.6/9.2 · where-to-get-it 11.6-13.4 · outro 13.4-16. Frames 1.5, 2.9, 7.8, 10.5, 12.2, 14.5 s.
- case (22 s): monitor + scene 0-3.2 (live ECG, blinking alarms) · question + options 3.2-6.2 · 3-2-1 countdown 6.2-9.2 · reveal 9.2-12.2 · why 12.2-17.2 · pearl + CTA 17.2-22.2. Frames 2, 4.5, 8, 10.5, 14, 20 s.

## Spec fields
Specs are JSON lists: `_src/tiktokN-am.json` (12:30) and `_src/tiktokN-pm.json` (20:30), one post per date each. Example: `tiktok-sample.json` (its old Amazon caption line is out of date; use the line below).

brand:
- `date` · `format` "brand" · `slot` · `product` · `label` (default SPOTLIGHT) · `chip`
- `hook` ≤ ~12 words · `kicker` one sentence · `points_title` · `points` exactly 3, ≤ ~10 words each
- `mockup` {`type`: meet | logbook | mindmap | guide | cards | books | bls | web, `title`, `labels` [...]}
- `where` (always the website) · `outro` · `tagline` · `caption`

case:
- `date` · `format` "case" · `slot` · `topic` (for the log) · `series` optional chip
- `vitals` up to 4 {`label`, `value`, `alarm`} · `scene` ≤ ~25 words · `question` · `options` exactly 4, ≤ ~6 words · `correct` "A"-"D"
- `why` ≤ 40 words · `pearl` ≤ 14 words · `cta` · `caption`

carousel: `date` · `format` "carousel" · `slot` · `topic` · `slides` (cover / body with header+bullets/body/pearl / cta, as in weekN.json) · `caption`. TikTok photo post: title = caption hook, autoAddMusic true.

## Caption rules (checked by gen_tiktok.py)
1. First line: scroll-stopping hook, under 100 characters (also the photo-post title).
2. 1-3 short teaching lines.
3. CTA: comment your pick / save / follow.
4. Exactly: `📚 More at www.anesthesiastudyco.com 🔗 link in bio`
5. 4-6 hashtags from #anesthesia #anesthesiastudent #crna #srna #caa #anesthesiastudyco, swapping in topic tags.
No Amazon/Etsy, no launch dates, no university/professor/exam names, no patient identifiers.

## Publishing (Metricool)
blogId 6389044 · providers [{"network":"tiktok"}] · autoPublish true · draft false · 12:30 or 20:30 America/New_York.
tiktokData: privacyOption PUBLIC_TO_EVERYONE · disableComment/Duet/Stitch false · isAigc false · autoAddMusic true on photo posts · title = caption hook line on EVERY post (Metricool rejects TikTok posts with no title, videos included) · commercialContentOwnBrand true (spotlights) / false (education).
Media: https://cdn.jsdelivr.net/gh/anesthesiastudycollc-cyber/ASC-Website@<hash>/tiktok/<am|pm>/<date>/reel.mp4 (+ videoThumbnailUrl .../cover.jpg) or .../slideN.jpg.

## Performance log
| Week | Views | Avg watch | New follows | Shares | Notes |
| --- | --- | --- | --- | --- | --- |
| Nov 19-25 | 318 | n/a | +1 (4 total) | 0 | Account's first 2 videos (both Nov 25, brand intros): 205 + 113 views, 1 like. |

## Topic log (no repeats within 8 weeks)
| Date | Slot | Format | Topic / angle |
| --- | --- | --- | --- |
| 2026-11-28 | 12:30 | case | Bezold-Jarisch: brady + hypotension in beach chair after interscalene |
| 2026-11-28 | 20:30 | brand | Spotlight: Meet ASC |
| 2026-11-29 | 12:30 | case | Peak 40 / plateau 18: resistance vs compliance |
| 2026-11-29 | 20:30 | case | PACU: sleepy, RR 6, SpO2 88% - airway and O2 first |
| 2026-11-30 | 12:30 | carousel | LAST: recognition to lipid emulsion (carousel) |
| 2026-11-30 | 20:30 | brand | Spotlight: Clinical logbooks and case trackers |
| 2026-12-01 | 12:30 | case | Quantitative TOF ratio 0.7 before extubation |
| 2026-12-01 | 20:30 | case | Auto-PEEP after bagging an asthmatic |
| 2026-12-02 | 12:30 | carousel | Venous air embolism: recognition and management (carousel) |
| 2026-12-02 | 20:30 | carousel | Spotlight: Quick Charts + quick-reference OR tools (carousel) |
| 2026-12-03 | 12:30 | case | TURP syndrome under spinal |
| 2026-12-03 | 20:30 | case | Bradycardia on laparoscopic insufflation |
| 2026-12-04 | 12:30 | carousel | 5 capnogram shapes (carousel) |
| 2026-12-04 | 20:30 | brand | Spotlight: Mind maps |
