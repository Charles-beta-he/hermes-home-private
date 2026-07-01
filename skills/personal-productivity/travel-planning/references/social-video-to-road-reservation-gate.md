# Social video → road reservation gate pattern

Use this when a user shares a short-form/social travel video or post claiming a road, scenic route, or access corridor now needs reservation/limited-entry control.

## Applicability

- Domestic self-drive or motorcycle route where access can be controlled by road authority, police, scenic-area management, or construction policy.
- User provides Douyin/Xiaohongshu/WeChat/social post/video that changes the operational plan: reservation, timed entry, permit, traffic restriction, vehicle class restriction, penalty, night closure, construction window, or entrance-specific control.
- The claim affects a hard route day, return buffer, lodging chain, or safety gate.

## Anti-conditions

- Do not treat social videos or reposted articles as final execution authority.
- Do not complete a reservation, payment, identity entry, SMS/CAPTCHA, or booking submission without explicit user action/authority.
- Do not turn a platform snippet into a certified gate if direct official readback or a user screenshot is required.
- Do not store trip-local details in memory; keep them in scoped TripState/SSOT.

## Procedure

1. **Extract the social claim.** Capture title, creator/source, publish time when available, URL, and the exact claim text/subtitles/comments that triggered the change.
2. **Classify the gate.** Decide if it is road/open status, reservation/permit, ticket, vehicle class, timed-entry, construction/night closure, penalty, or route-safety gate. Reservation/permit and road status should be high-risk dynamic gates.
3. **Search for stronger authority.** Look for official or semi-official readback: road authority, police/traffic, government, official WeChat, platform announcement, or local official account. Search snippets can strengthen evidence but remain advisory if the primary source is not directly opened/read.
4. **Patch the TripState, not memory.** Add a scoped evidence item with status such as `advisory`, `needs_official_readback`, or `official_screenshot_required`; add a gate before the route/weather/fuel gates when access permission is prerequisite.
5. **Make the gate fail-closed.** If reservation/permit is missing, stale, entrance/time-slot mismatch, platform unavailable, or after the allowed entry window, route to fallback; do not let road/weather pass override access failure.
6. **Preserve execution evidence requirements.** Ask the user for an official platform screenshot/readback containing the minimum necessary fields: date, entrance, time slot, vehicle/driver info (may be masked), status/validity, and source/channel.
7. **Test the behavior if productized.** Add assertions that unknown reservation gates produce warning/requested evidence, that reservation gates are high-risk dynamic gates, and that fresh evidence is advisory unless independent certification votes are supplied.

## Output shape

When reporting back:

- What the video/social source says.
- What stronger official/semi-official evidence says.
- Evidence status: advisory / official snippet / direct official readback / certified.
- Exact TripState gate added.
- Execution rule: all conditions to proceed; fail-closed fallback.
- Human gate: what screenshot/official record is needed before day-of execution.

## Example pattern

For a Duku-style route day:

```text
D8-DUKU-RESERVATION
category: reservation
source: social_video + official-search snippet
status: needs_official_readback
hard rule: official reservation success + matching entrance + matching time slot + before night/construction closure
fallback: do not enter the road segment; route around or retreat to safe lodging
```

Even if reservation evidence says `pass`, it only clears the access gate. Road opening, weather, fuel, driver state, and arrival-time gates still apply.
