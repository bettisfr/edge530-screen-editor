#!/usr/bin/env python3
__version__ = "2.8.0"  # LAYOUT GEOMETRY CONSOLIDATED HERE, and made PER SCREEN TYPE (2026-09-10) -- this file is now the single source for which field positions share a row, which (count, variant) states are legal, and where a named screen's device-generated content area sits. Until now that knowledge was SPLIT: gui_app.py owned LAYOUT_GRIDS (the diagram and the full-width advisories) while fit_patch.py owned COUNTS_WITH_B_VARIANT (which counts have a real A/B choice). Nothing forced them to agree and they drifted, invisibly, because each was internally consistent. Both now import from here; fit_patch.py keeps COUNTS_WITH_B_VARIANT as a re-export for anything already referencing it. New NAMED_SCREEN_LAYOUTS table, from a COMPLETE on-device survey of all 12 named types (Doug, Edge 530, 2026-09-08 -> 2026-09-10, PROJECT_NOTES.md Doc rev 112): each entry holds the exact (field_count, f8_variant) pairs the device's own selector offers, in its order, plus that count's row structure and the content area's position. Four things this code treated as global constants are per type: the grid (count -> rows became type+count -> rows), the A/B choice (a fixed {3,4,5,6,7} became per type), the MINIMUM count (1 hardcoded; Map and Segment legally hold ZERO fields, rendering full-screen), and the MAXIMUM (10; four types are fixed at exactly 2, and Segment accepts only even counts 0/2/4/6). Every (count, f8) pair is MEASURED, never derived, and the reason is Segment: its 4-field layout that the on-device menu labels "A" stores f8=2, not 0. That was found only by saving 4/A, pulling the file, saving 4/B and pulling again -- the two differed by exactly one byte plus the CRC, at mesg 14 field 8. A single 4/B pull would have left the old A=0/B=1 assumption intact and wrong, which is why layout_default_variant() returns a stored value rather than computing one. New query helpers (named_layout, layout_states, layout_grid, layout_counts, layout_state_is_valid, layout_variants_for_count, layout_default_variant, count_is_locked, content_area_position) and DEFAULT_FILLER_FIELD_ID=56 "Timer", stamped into slots when a layout change grows a screen. is_position_full_width() gains an OPTIONAL TRAILING f10 -- optional for backward compatibility, but passing it matters: without it every screen is measured against ordinary-user-screen geometry, where 2 fields are two STACKED FULL-WIDTH rows, whereas every fixed-2 named type renders two HALF-WIDTH fields side by side. Since that function also feeds the Graph/Bars and Connect IQ half-width advisories, all three were wrong together on those screens before this. Any f10 ABSENT from NAMED_SCREEN_LAYOUTS falls through to the previous behaviour, so ordinary user screens are byte-for-byte unaffected and a named type on some future Edge model degrades gracefully rather than erroring. The three types with no editable fields (26, 38, 57) deliberately get NO entry -- NO_FIELD_EDIT_TYPES already handles them, and an empty-states entry would imply their count is merely constrained rather than absent. Prior entry (2.7.0): New NO_FIELD_EDIT_TYPES constant (2026-09-09), currently {26, 38, 57} -- "Virtual Partner", "Workout" and "GroupTrack List" -- screen types that hold NO user-editable data field array at all, because the device generates their entire contents itself. Doug's report: selecting GroupTrack List in the GUI and pressing "Add Field..." opened the normal field picker, which it should not -- that screen renders the list of connected GroupTrack/LiveTrack riders, and every one of the 17 profiles this project has on hand carries it at f3=0 without exception. DISTINCT from FIELD_EDIT_UNCERTAIN_TYPES, which is a non-blocking WARNING for types whose field bytes are real and readable but whose on-device rendering is unverified; NO_FIELD_EDIT_TYPES is a HARD BLOCK, because there is no field array to edit in the first place -- offering the controls is wrong rather than merely unproven. That warning set is now EMPTY, because its only member, 38 "Workout", was PROMOTED into this hard-block set on 2026-09-10 after Doug confirmed on-device that it too offers no editable data fields -- the set and its warning machinery are deliberately KEPT as the home for any future type in that situation. Workout's promotion also settles a methodological point worth recording: it carries f3=2 with a real, readable field array (byte-for-byte identical to Cycling Dynamics' on the same profile), GroupTrack List carries f3=0, and Virtual Partner carries f3=255 -- three DIFFERENT f3 values with identical "no editable fields" behaviour, which is conclusive that f3 content cannot be used to infer this property. Only the on-device editor can. Enforced in fit_patch.py v1.16.1 (any f3/f7/f8 write, no --force override) and gui_app.py v0.21.2 (which also greys the field controls rather than only refusing on click). Virtual Partner (f10=26) was added the same day, after Doug checked the ON-DEVICE editor directly and confirmed its screen-edit section offers no user-editable data fields and no preview-screen option -- the same treatment GroupTrack List gets. That direct check is what promoted it from "likely" to a hard block: the file evidence alone was ambiguous, since Virtual Partner carries f3=255 (the uint8 unset sentinel) rather than GroupTrack List's clean f3=0. The set stays growable, with that same on-device-confirmation bar for anything added later. Show/Hide and --swap-order are deliberately unaffected for these types: hiding or reordering GroupTrack List is legitimate. No existing data changed. Prior entry (2.6.0): Connect IQ marker constant RENAMED and its meaning CORRECTED (2026-09-06) -- DEVICE_DEPENDENT_CIQ_IDS is now CIQ_FIELD_MARKER_IDS, with the old name kept as a backward-compatible alias so any external script still importing it keeps working. The rename follows a real correction, not a style preference: the old name was wrong on both words. Field 216 is neither device-dependent nor an app identity -- it is a GENERIC "a Connect IQ data field goes here" type marker. CONFIRMED (Doug, real Edge 530) by placing two DIFFERENT Connect IQ apps on the SAME screen at adjacent positions simultaneously: both stored as 216. The earlier reading (Doc rev 95-97) that 216 was a device-local, install-order-reassigned per-app identity was inferred from watching the same id appear to mean a paid app and later a free one on one device; what actually changed between those observations was the set of mesg_num=170 records around a marker that never meant either app. All Connect IQ app identity lives in those records -- each carries one app's UUID plus a packed list of the exact (screen slot, field position) pairs it occupies; see fit_patch.py v1.16.0's read_ciq_records()/ciq_entry() for the decoded format, and PROJECT_NOTES.md Doc rev 103-108 for the investigation and the on-device confirmations. The device renders Garmin's generic "Timer" fallback at any position holding this marker that no mesg 170 entry claims, which is exactly what every pre-v1.3.0 toolkit write produced. No data change in this file: FIELD_ID_NAMES[216] remains the generic "CIQ Data Field", the set still contains only {216}, and every read/display path is unaffected. Prior entry (2.5.0): Device-dependent Connect IQ field handling, Doug's explicit request (2026-09-02), following the WindField/Edge 3270 investigation (PROJECT_NOTES.md Doc rev 95-99): real-hardware testing confirmed field 216's identity is DEVICE-local and install-order-reassigned (the same numeric ID meant a paid app, then a completely free one, on the same device after reinstalling), not a stable per-app name -- and that this toolkit cannot write one into a slot at all, whether fresh or already-occupied. New DEVICE_DEPENDENT_CIQ_IDS constant (currently {216}), deliberately growable for future-discovered IDs on other devices/apps. FIELD_ID_NAMES[216] renamed from the misleading, occasionally-wrong "WindField Widget" to a generic "CIQ Data Field" -- a DISPLAY-only change; this dict is still the single source read directly by this file's own `screens`/`dump` output and the GUI's read-only views, unaffected by the separate write-side hard refusals added the same date to fit_patch.py (v1.15.0) and gui_app.py (v0.20.0). Prior entry (2.4.25): CONFIRMED via GUI, real hardware (2026-08-22): Doug spot-checked the field picker in gui_app.py directly against several of the 2026-08-20 batch additions (137->169 entries across three batches that day) and confirmed the labels shown match what's on-device -- closes the loop from "present and correctly typed in the dict" to "actually wired through and displayed correctly in the running GUI." No dict values changed, confirmation-only entry. Prior entry (2.4.24): Add 13 confirmed field IDs, 2026-08-20 batch #3, Doug's cross-check of his confirmed-field list against the Garmin Edge 530 Owner's Manual's own data-field appendix: 98 Watts/kg, 439 3s W/kg (3s Watts/kg), 207-213 Power Z1-Z7, 418 Power Z8, 419 Power Z9 (Time in Power Zone 1-9, the Power-Zone analog of the existing 199-203 HR Zone 1-5 (time) fields -- 9 zones not 5), 24 Laps, 41 Max Lap Power (resolves an earlier ambiguous "Laps Max" note -- turned out to be two separate fields Doug had conflated, not one oddly-named field). Fills the last two gaps in the W/kg family (base metric + 3s variant, was Avg/10s/30s only) and extends Power's own Lap/Max/Last-Lap set with the one remaining combination. No collisions with any existing entry (confirmed via AST parse before insertion). Closes out Doug's manual-appendix cross-check -- no further appendix-listed fields remain unconfirmed. FIELD_ID_NAMES now 169 confirmed entries (was 156). One real gap still open, NOT part of this batch: "Trainer Resistance" -- working hypothesis, unverified, is that it needs a paired ANT+ FE-C smart trainer to appear in the on-device picker at all, same sensor-gated pattern as eBike Metrics; Doug doesn't have one to test against currently. Same-batch comment fix (fit_dump.py only, no data change): corrected a factual error in the v2.4.23 changelog/inline comment, which wrongly said the pre-existing W/kg family included field 159 -- 159 is actually "3s Balance," an unrelated field; the real pre-existing W/kg family was just 437/441. Prior entry (2.4.23): Doug's continued field census: 265 Lap PCO, 267 Avg Right PP, 268 Lap Right PP, 269 Right PPP, 271 Lap Right PPP, 273 Avg Left PP, 274 Lap Left PP, 275 Left PPP, 277 Lap Left PPP, 440 10s W/kg. Fills out the L/R Power Phase/Peak Power Phase family alongside the existing 263/264/266/270/272/276 entries -- no collisions with any existing entry (confirmed via AST parse before insertion). FIELD_ID_NAMES now 156 confirmed entries (was 146). Doug provided each field's full concept name alongside its on-device label this time (e.g. "Avg Right PP" = "Avg Right Pwr Phase") -- values stored are the on-device labels per this dict's established convention, full names recorded in the inline comment for reference. Same batch, doc-only: Doug investigated the one remaining unmapped on-device label he'd been tracking, "Battery Status" (Lights category) -- confirmed it's an alias/duplicate menu entry that navigates straight to the SAME field as 317 "Light Battery", not a separate field; noted inline at 317's entry, no new dict entry added or needed. Prior entry (2.4.22): Correction, same day, Doug's own catch (2026-08-20): the 2026-08-20 batch's "Target" field was mistyped as ID 512 -- Doug confirmed the real ID is 521 (512 never existed on-device under either name; a simple mistyped digit, not a raw-ID/name mismatch the way the 2026-08-17 screen-3/4 transposition was). Corrected before this ever shipped in a tagged release. Doug also confirmed, unprompted, that all 9 fields from that batch (not just the corrected one) are verified against the real on-device screen -- same confirmation standard as every other batch here, upgrading the batch's status from "field names, not yet independently stress-tested" to fully confirmed. No count change, still 146 entries (was a mistyped key, not a new/removed ID). Prior entry (2.4.21): Add 9 confirmed field IDs, 2026-08-20 batch, Doug's continued field census: 521 Target (see correction above), 523 Step Time, 522 Duration, 511 Workout Comparison, 45 Workout Step, 100 Last Lap Power, 258 Lap Time Standing, 260 Lap Time Seated, 264 Avg PCO. No collisions with any existing entry (confirmed via AST parse before insertion). Notable: 5 of these 9 (45, 511, 521, 522, 523) read by name as Workout/structured-step fields (Workout Step, Workout Comparison, Target, Duration, Step Time) -- directly adjacent to this project's still-open f10=38 "Workout" SCREEN-TYPE question (FIELD_EDIT_UNCERTAIN_TYPES, gui_app.py's field_edit_uncertain_warning_text() warning, see PROJECT_NOTES.md Open Items): whether that screen's field slots are actually meaningful/rendered on-device, since the on-device editor exposes no field options for it at all. That's a separate, still-unconfirmed question from these fields' own identity, which Doug's on-device verification establishes with the same confidence as any other entry in this dict. The other 4 (100 Last Lap Power, 258/260/264) extend already-populated families: Power (100, matching the existing 3s/10s/30s/Lap/Avg pattern) and Cycling Dynamics (258/260/264, standing/seated lap time + PCO). FIELD_ID_NAMES now 146 confirmed entries (was 137); KNOWN_UNRESOLVED_IDS still empty. Prior entry (2.4.20): FULLY CONFIRMED via direct raw-byte inspection (2026-08-17, same day as v2.4.19): Doug's CyclingRoadRoadtemp.fit -- the original census profile itself, with Screen 3 (slot 6) and Screen 4 (slot 7) still intact at their full 10 fields each -- came through on a second upload attempt and was dumped directly via `fit_dump.py dump`. Raw field-ID arrays: 14[6].7 = [150, 149, 177, 176, 43, 437, 40, 408, 411, 441] (Screen 3), 14[7].7 = [80, 42, 148, 147, 82, 83, 151, 161, 160, 159] (Screen 4). Every one of the 20 corrected (ID, name) pairs from v2.4.19 matches these raw arrays position-for-position exactly -- including field 177 "Torque Effect" under its own ID, closing the one residual flag v2.4.19 was still carrying (that string had only been confirmed against ID 148 before the transposition was found). This is now the same direct byte-level verification standard as every other confirmed batch in this dict, no longer resting on the 3-for-3 device-observed inference alone. No dict values changed from v2.4.19 -- this entry is the independent confirmation that was pending. Prior entry (2.4.19): RESOLVED, Doug's own diagnosis (2026-08-17, same day as the v2.4.18 flag): the entire 2026-08-17 field-ID batch had its raw IDs and names correctly IDENTIFIED but WRONGLY PAIRED -- Doug's census screens 3 and 4 (Roadtemp profile) got transposed when the original list was written up, so all 10 IDs from one screen's block were paired with the 10 NAMES from the other screen's block (a clean systematic offset, not scattered errors -- the SET of 20 raw IDs is unchanged, only which name each points to). Doug re-derived the correct pairing directly from Roadtemp's screen 3/4 field order; it resolves ALL THREE real-device mismatches from v2.4.18 exactly (437 -> Avg W/kg, 147 -> Lap NP, 148 -> Last Lap NP, all now matching the device precisely). All 20 dict entries corrected; SUSPECT warnings removed. One residual flag: field 177 (now "Torque Effect", the string confirmed via v2.4.17's half-width-field test) was NOT independently re-tested under ITS OWN ID after the swap was found -- that confirmation was made against ID 148 before the transposition was discovered, so it's carried over on the strength of the transposition theory rather than a fresh direct test. Not independently re-confirmed via a raw byte-level dump either (attempted -- Doug's uploaded CyclingRoadROAD.fit/CyclingRoadRoadtemp.fit weren't readable in this session, an environment sync issue, same as the earlier CyclingEbike.fit episode) -- treated as sufficiently confirmed on the strength of the 3-for-3 exact match against independently-observed real device behavior. No count change, still 137 confirmed entries -- this is a re-pairing, not new/removed IDs. See PROJECT_NOTES.md Open Items and "Corrections and lessons learned" for the full writeup. Prior entry (2.4.18): URGENT flag, no value changes yet, Doug's report from actually checking the device: editing Screen 4 (slot 7) via the GUI to [437 "Intensity Factor (IF)", 147 "Pedal Smoothness", 148 "Torque Effect", 320 "Perf. Conditioning"] produced a screen that ACTUALLY displays "Avg W/kg, Lap NP, Last Lap NP, Perf. Cond." on the real device -- 3 of 4 wrong (320 is fine, just further-truncated display of the same correct name). Reviewed FieldPickerDialog directly (gui_app.py): no indexing/lookup bug there, it writes exactly the raw ID paired with the selected name, so this dict itself had wrong ID->name associations for at least 437/147/148, most likely a census/transcription error from how the 2026-08-17 batch (v2.4.16) was originally verified, not a code bug in the read/write/picker path. Since this dict already had separate entries for "Avg W/kg" (83), "Lap NP" (176), "Last Lap NP" (177) from the SAME batch, those three were the leading candidates for the TRUE identity of whatever raw IDs were actually stored at those 3 slot-7 positions -- confirmed correct by v2.4.19 above. Added prominent inline warnings marking the ENTIRE 2026-08-17 batch (all 20 entries) UNCONFIRMED/SUSPECT pending re-verification -- only 4 of 20 had been checked against a real device at that point and 3 were wrong. Prior entry (2.4.17): field 148 was stored as "Torque Effect." (a GUESSED abbreviated form, by analogy to field 320's "Perf. Conditioning" convention) -- Doug directly confirmed the real on-device text in a half-width (1/2 side-by-side) field is "Torque Effect", no trailing period. Corrected. No count change, still 137 confirmed entries -- this is a text correction, not a new/removed ID. FIT_PATCH.md's FIELD ID REFERENCE table and NOTE updated to match. Prior entry (2.4.16): Add 20 confirmed field IDs, 2026-08-17 batch, Doug's continued field census (this project's first batch touching power-meter/Di2-electronic-shifting metrics): 42 Balance, 80 Avg Balance, 40 Lap Balance, 441 3s Balance, 411 10s Balance, 408 30s Balance, 150 30s Power, 151 Max Power (reported "MAX Power," normalized to Title Case matching this dict's existing "91: Max Speed" convention), 83 Avg W/kg, 159 30s W/kg, 149 %FTP, 43 TSS, 437 Intensity Factor (IF), 176 Lap NP, 177 Last Lap NP, 148 Torque Effect. (reported full concept name "Torque Effectiveness (Torque Effect.)," stored abbreviated per this dict's on-device-display convention, e.g. 320 "Perf. Conditioning"), 147 Pedal Smoothness, 82 Power Zone, 161 Di2 Battery, 160 Di2 Shift Mode. Notable: confirms the Power family's 3s/10s/30s/Lap/Avg naming pattern (79 "3s Power", 146 "10s Power", both pre-existing) repeats identically for L/R Power Balance, with 42 "Balance" as the base metric mirroring 36 "Power" -- a clean, self-consistent family, not a set of one-off guesses. No collisions with any existing entry (confirmed via AST parse before insertion). FIELD_ID_NAMES now 137 confirmed entries (was 117); KNOWN_UNRESOLVED_IDS still empty. gui_app.py's FieldPickerDialog docstring (stale "117 confirmed entries") updated to match -- same recurring drift class as v0.16.5/v0.16.12's fixes, FIELD_ID_NAMES is imported live so only the comment was ever wrong. Prior entry (2.4.15): FIELD_EDIT_UNCERTAIN_TYPES = {38} ("Workout"), backing a new EditScreenPanel warning (gui_app.py v0.19.4). Doug raised a real concern: this screen doesn't show in the on-device scroll list during a normal ride (same conditional-trigger family as ClimbPro/Segment), so there's no way to see what editing its fields is actually supposed to look like -- worth flagging before offering the edit, not after. Backed by Garmin's own Edge 530 manual (Training > Workouts: starting a Workout "displays each step of the workout, the target (if any), and current workout data"), confirming the leading hypothesis from v2.4.14: "Workout" is almost certainly Garmin's structured-workout step display, a separate subsystem from Activity Profile screens entirely, only live while a Workout (GARMIN/Workouts/Guided or /Scheduled, synced via Garmin Connect or built on-device) is actively running -- matching Doug's own device having both Workouts subfolders empty (he's never used the feature, hence never seen this screen render). Deliberately a WARNING, not a hard block (unlike Map/ClimbPro's Show-toggle guard, which is backed by independent on-device confirmation neither has a toggle at all) -- the write mechanism itself is the same proven-safe path used for every other screen type, so the real risk here is a pointless/no-visible-effect edit, not device corruption, and only one profile's worth of evidence exists so far. Prior entry (2.4.14): CORRECTION to v2.4.13, same day (2026-08-16), Doug's uploaded CyclingEbike.fit now inspected directly: v2.4.13 added NAMED_SCREEN_TYPES keys 39/59/96, but those were WRONG -- Doug (and this project, before having the raw file) read those numbers off this tool's own "Screen N" fallback label, which is f10+1 (screen_type_name()'s documented convention), not the raw f10 byte. The REAL f10 values, confirmed via a direct raw dump of the actual file, are 38 "Workout" (was displaying as "Screen 39" = 38+1), 58 "eBike Metrics" ("Screen 59" = 58+1), 95 "STEPS Metrics (Shimano)" ("Screen 96" = 95+1). v2.4.13's keys of 39/59/96 would NEVER have matched these real values -- a real bug that shipped and did nothing, caught before Doug pulled the updated file (screen_type_name(39)/(59)/(96) were simply never reached, since no real profile has those exact f10 values; the display would have silently kept showing "Screen 39" etc., appearing to work purely because 39/59/96 happen to equal 38+1/58+1/95+1). Corrected all three keys to 38/58/95. Also RESOLVED, not just flagged, the f10=38 "Workout" field-reading question from v2.4.13: CONFIRMED via direct raw dump comparison (not just field-name matching) that slot 6's f10=38 record's field-ID array is byte-for-byte IDENTICAL, all 10 positions, to slot 1's Cycling Dynamics (f10=63) record on the SAME profile -- this is real, accurately-read data, not a classify_screens()/active_field_ids() bug (those functions are working correctly; the underlying bytes genuinely are a copy). Also found, while inspecting the raw dump: the two REMOVED screens with non-empty field content (slots 11 and 12) are ALSO byte-for-byte identical to the two currently-ACTIVE f10=58/95 records (eBike Metrics/STEPS Metrics) -- three confirmed exact-duplicate pairs on one profile, not a single coincidence, consistent with Garmin auto-creating these e-bike/third-party-sensor-triggered screen types from a fixed default field template each time, the same way Map/Elevation/ClimbPro already do. No code behavior change beyond the corrected dict keys -- classify_screens()/active_field_ids() were never wrong, this was purely a wrong-value bug in the new NAMED_SCREEN_TYPES entries themselves. See PROJECT_NOTES.md Open Items for the full writeup and the still-open product question (should editing f10=38 "Workout" fields via this toolkit be guarded/warned, since the on-device editor doesn't expose them at all). Prior entry (2.4.13, SUPERSEDED, kept for the record): New confirmed f10 screen types, 2026-08-16 batch (Doug, CyclingEbike.fit -- the first e-bike/third-party-drivetrain profile this project has seen): NAMED_SCREEN_TYPES gains 39 "Workout", 59 "eBike Metrics", 96 "STEPS Metrics (Shimano)" -- no collision with any existing entry (63 "Cycling Dynamics" is the nearest neighbor and is unaffected; note field ID 39 already exists in the SEPARATE FIELD_ID_NAMES dict as "Lap Power" -- a numeric coincidence across two independent namespaces, f10 screen-type identity vs. data field ID, not a real collision, same non-issue this project has flagged before for field 58/84). FLAGGED, NOT YET RESOLVED: Doug reports f10=39 "Workout" behaves unlike every other named type here -- the on-device screen editor shows no fields/options for it at all (only Remove/Reorder Screen), but this toolkit's own screens/edit-screen views show it with the same field set as a Cycling Dynamics screen on the same profile. Not yet independently verified against the raw file (this session's attempt to inspect Doug's uploaded CyclingEbike.fit directly did not succeed -- environment/upload issue, not investigated further yet), so no behavior change made for this type; screen_type_name(39) now correctly labels it "Workout," but classify_screens()/field reading are UNCHANGED pending real byte-level investigation. Leading hypothesis, unconfirmed: f10=39 may be a Garmin SYSTEM screen type like Map/ClimbPro whose field-slot bytes aren't actually meaningful/rendered by the device (matching the f10=32 "Reserved" record's own always-present-regardless-of-content pattern), rather than a real field-reading bug -- needs the raw bytes to confirm either way. See PROJECT_NOTES.md Open Items. Prior entry (2.4.12): Rename only, Doug's decision (2026-08-15): NAMED_SCREEN_TYPES[32] renamed from "GroupTrack" to "Reserved" -- this f10=32 record is a Conditional-only runtime record present on every profile seen so far, active or not, regardless of whether GroupTrack has ever actually been used, and its real purpose was never independently confirmed (unlike f10=57 "GroupTrack List," the literal on-device menu entry for the feature, which is unaffected by this rename and remains correctly GroupTrack-specific). Updated every surrounding comment/docstring in this file that asserted or implied f10=32 was confirmed GroupTrack's own record (NAMED_SCREEN_TYPES' own comment block, classify_screens()' docstring and inline comments, the `screens` subcommand's CLI section header/verbose note) to instead describe it accurately as an always-present record of unclear purpose -- no functional/behavioral change anywhere, screen_type_name(32) now just returns a different string. gui_app.py and fit_patch.py's own comments referencing this record updated to match in the same pass (see their own changelogs). Prior entry (2.4.11): New constant, no existing behavior change (2026-08-14): added GRAPH_OR_BARS_FIELD_IDS -- the 10 fields individually confirmed on-device (2026-08-11, Doug) to render as a Graph/Bars widget that only actually draws that way in a full-width screen slot (23, 343-350, 368). Kept as its own set, separate from FIELD_ID_NAMES, per the "Graph/Bars full-width warning" Open Item's design -- avoids touching every existing consumer of FIELD_ID_NAMES just to add a category flag. Backs the new gui_app.py warning (v0.16.15) surfacing this in FieldPickerDialog and EditScreenPanel/AddScreenPanel. No FIELD_ID_NAMES entries changed, still 117 confirmed entries. Prior entry (2.4.10): doc-only, no functional change (2026-08-13): updated the verbose "Removed screens" note in the `screens` subcommand -- it referenced fit_patch.py's --un-remove flag, which Doug decided to retire entirely (see fit_patch.py v1.13.0's changelog for the full reasoning: Restore-from-Backup already covers real recovery, --un-remove had a confirmed historical data-loss hazard that was never re-verified, and Garmin's own editor doesn't offer an un-remove workflow either). Note now points to Restore-from-Backup instead of a flag that no longer exists. Prior entry (2.4.9): bug fix, real user report (2026-08-11): field 320 was "Conditioning" -- incomplete. The full concept name is "Performance Conditioning," but Doug confirmed the actual on-device DATA FIELD display reads "Perf. Conditioning" (abbreviated). Corrected to match this toolkit's established convention of naming fields as they display on-device rather than by their full/conceptual name (same convention behind "Lap Dist.", "Dest. Location", etc.). FIELD_ID_NAMES still 117 entries (rename only). Prior entry (2.4.8): bug fix, real user report (2026-08-11): field 49 was "Avg Speed (Alt)" with no record of how/why -- predates this project's discipline of noting confirmation method per field, same blind spot as field 58's earlier wrong "Lap Timer" guess. Doug deployed it into a full-width screen slot via the GUI and visually confirmed on-device: plain text "Avg Speed," no graph or bars. Corrected to "Avg Speed." IMPORTANT METHODOLOGICAL NOTE, not just a rename: this is a caution for the Graph/Bars "*"/"(Alt)" marker theory (v2.4.6/2.4.7) -- unlike 23/348/349, there's no record 49's old "(Alt)" label was ever a literal transcription of a real on-device marker, so this doesn't necessarily falsify the theory, but does mean an OLD placeholder name merely containing the word "(Alt)" isn't itself evidence of a real on-device marker unless that was actually recorded at the time. FIELD_ID_NAMES still 117 entries (rename only, no count change). See PROJECT_NOTES.md "Graph/Bars full-width warning" for the updated caution. Prior entry (2.4.7): add 12 confirmed field IDs, 2026-08-11 batch: 2 Course Pt Dist., 15 Lap HR, 18 Lap %Max HR, 32 Next Pt Location, 165 Last Lap HR, 347 HR Bars, 350 Power Bars, 433 Anaerobic TE, 452 Respiration, 478 EPOC, 495 60s Grit, 497 60s Flow -- from Doug's continued field census in a separate session, same direct on-device verification standard as every prior batch. Also corrects 3 placeholder names that were built around the "*"/"(Alt)" marker before its meaning was confirmed: 23 "Heart Rate (Alt)" -> "HR Zone Graph" (a distinct Graph-type field, not an alternate view of plain Heart Rate), 348 "Speed *" -> "Speed Bars", 349 "Cadence *" -> "Cadence Bars" (marker confirmed as Bars-type, not Graph -- see the field 23/343-350 comments). No collisions with any existing entry (confirmed via AST parse before insertion). FIELD_ID_NAMES now 117 confirmed entries; KNOWN_UNRESOLVED_IDS still empty. Prior entry (2.4.6): doc-only, no functional change (2026-08-11): the long-open "*" marker mystery on fields 348/349 (Speed */Cadence *) is LIKELY RESOLVED -- Doug reported confirming that "*" (and separately "(Alt)", seen on fields 23/49) marks a Graph- or Bars-style rendering that needs a full-width screen slot to actually draw as a graph/bar, falling back to plain text otherwise. Not yet independently re-verified by this project across multiple placements, so treated as the working explanation rather than stated as certain -- comments updated accordingly (348/349's block above, this entry). No FIELD_ID_NAMES entries changed. See PROJECT_NOTES.md "Graph/Bars full-width warning" (Open Items) for a scoped GUI feature this unlocks. Prior entry (2.4.5): bug fix, real user report (2026-08-11): fields 58 and 87 were transcribed as "Lap Timer" and "Last Lap Timer" -- Doug's own earlier assumption by analogy to the separate, correctly-named field 56 "Timer" -- but a closer on-device relabeling check found the real display text is "Lap Time" and "Last Lap Time," no "r." Corrected in FIELD_ID_NAMES (58, 87) and their surrounding comments (including the KNOWN_UNRESOLVED_IDS resolution note for 84/87). Field 56 "Timer" is unaffected and still correct. No new/removed field IDs, still 105 confirmed entries. FIT_PATCH.md's FIELD ID REFERENCE table and NOTE sections corrected to match (now doc rev 12). Prior entry (2.4.4): add 18 confirmed field IDs, 2026-08-10 batch: 7 Lap Dist., 30 Time to Next, 31 Dest. Location, 39 Lap Power, 50 Lap Speed, 57 Avg Lap Time, 61 Total Descent, 62 Dest. Ahead, 63 Time Ahead, 67 Reps to Go, 86 Last Lap Speed, 88 30s VAM, 94 ETA to Next, 95 Odometer, 295 Target Power, 442 Lap VAM, 443 Avg VAM, 445 Asc to Next Crs Pt -- developer arranged two screens to 10 fields each on a real profile specifically for this census, entered/selected each field by its on-device name, then cross-referenced every field's raw ID against its known on-screen position using the GUI (v0.16.4's readability/resize fixes were what made that cross-referencing practical -- see gui_app.py). No collisions with any existing FIELD_ID_NAMES entry (confirmed via grep before insertion). FIELD_ID_NAMES now 105 confirmed entries; KNOWN_UNRESOLVED_IDS still empty. Prior entry (2.4.3): add 1 confirmed field ID (58, Lap Timer) -- surfaced incidentally by real GUI Restore-from-Backup testing (an old 8/3/2026 backup had a field the GUI's picker didn't recognize), confirmed via direct visual comparison against the live device display. FIELD_ID_NAMES now 87 confirmed entries. Prior entry (2.4.2): add 2 confirmed field IDs closing the last open field-ID mystery (84 Last Lap Dist, 87 Last Lap Timer -- note: unrelated numeric coincidence to this entry's field 58, "Last Lap Timer" vs. "Lap Timer" are genuinely distinct fields, not a naming collision), confirmed via a forced-field test deployed successfully through NewFiles -- FIELD_ID_NAMES was 86 confirmed entries; KNOWN_UNRESOLVED_IDS still empty
"""
fit_dump.py - Dump (and diff) Garmin .FIT files for reverse-engineering
undocumented messages/fields, e.g. Edge Sports/<Profile>.fit data-screen
and data-field layout.

Uses garmin_fit_sdk (official Python SDK: `pip install garmin-fit-sdk
--break-system-packages`). Known messages/fields decode with their real
names via the public Profile; anything NOT in the public Profile.xlsx
comes through keyed by its raw numeric global_mesg_num / field number
(e.g. message key "147", field key 254) instead of being dropped -- that
raw numeric output is exactly what you diff to find undocumented
screen/field-layout messages.

USAGE
-----
Dump a single file to a stable, diff-friendly text form:
    python3 fit_dump.py dump baseline_A.fit > A.txt
    python3 fit_dump.py dump baseline_B.fit > B.txt
    diff A.txt B.txt

Or let the script do the dump + diff in one step:
    python3 fit_dump.py diff baseline_A.fit baseline_B.fit

Show only messages the public FIT profile doesn't recognize
(these are your reverse-engineering targets):
    python3 fit_dump.py unknown baseline_A.fit

Notes
-----
- Output is sorted (message key, message occurrence index, field key) so
  that two dumps of files that are semantically identical produce
  byte-identical text, and `diff` only shows what actually changed.
- Multi-value / byte-array fields are rendered as compact repr() so they
  diff cleanly on one line instead of exploding into multiple lines.
- Decoder errors (bad CRC, truncated file, etc.) are printed to stderr
  but don't abort the dump -- partial data is still useful when you're
  poking at a device that might reject a hand-edited file.

GUI reuse
---------
classify_screens() and active_field_ids() are plain, print-free
functions that return Python data structures -- safe to import
directly (`from fit_dump import decode_file, classify_screens,
field_name`) from the GUI or any other in-process consumer, with no
subprocess call and no text to parse back out. cmd_screens() is just
the CLI's own consumer of the same two functions; its printed output
is unchanged by this split.
"""

import sys
import argparse
from garmin_fit_sdk import Decoder, Stream

# [VERIFIED S1] mesg_num=14 == data_screen, one message instance per screen
# slot. Confirmed via byte-level diff of three known-good Road profile
# copies (single isolated field-count edits) and independently re-validated
# against a second, structurally different Gravel profile with zero
# misreads.
DATA_SCREEN_MESG_KEY = "14"

# [VERIFIED S1] Field layout within a data_screen message:
#   254 = message_index (screen slot number, 0-based)
#   3   = active field count (uint8). Key is ABSENT ENTIRELY (not present
#         in the dict at all) on unconfigured/preallocated-but-empty slots
#         -- confirmed via garmin_fit_sdk output, not a literal 255.
#   7   = 10-slot list of field IDs (uint16). Only the first field_count
#         entries are active; trailing entries are leftover/default values
#         or None (SDK's decode of the FIT uint16 invalid sentinel 0xFFFF)
#         and are NOT meaningful past field_count.
#   1, 9, 10, 11 exist but semantics are NOT yet confirmed. Field 1
#   is NOT the enable/disable flag (always 1 on populated slots) -- that
#   mechanism is field 12, see below.
# [VERIFIED S4] field 12 = enabled/disabled flag (uint8). 0 = enabled
#   (shown in the on-device Data Screens list), 1 = disabled/hidden.
#   Confirmed two ways: (a) in the original baseline, Slot 1 (Lap
#   Summary) was the ONLY screen with f12=1, and the developer's own
#   ground-truth device check independently marked that exact screen
#   OFF while every f12=0 screen was ON; (b) toggling Lap Summary's
#   on-device enable switch flipped
#   f12 from 1 -> 0, isolated to this single byte with no other change
#   to the message. This resolves the earlier mystery of why "OFF"
#   screens still carry real, valid field data (they're just marked
#   disabled, not cleared).
# [VERIFIED S3] field 8 = layout_variant (uint8). 0 = default/"A" grid
#   layout for the current field_count; 1 = alternate/"B" layout (e.g.
#   an on-device #6-A -> #6-B change for Slot 4, isolated to this
#   single byte via before/after message diff, confirmed 0 on every
#   never-edited screen in the baseline profile). Only 0/1 confirmed so
#   far -- layouts with more than two named variants (if any exist) may
#   use higher values, unconfirmed.

# Confirmed field-ID -> display name. Built and cross-validated across
# Road, Gravel, and Tourtst profiles -- multiple independent screens
# agreeing on the same ID -> name mapping, plus on-ride visual
# verification for several graph-type fields (see note on 344/346 below).
FIELD_ID_NAMES = {
    0:   "Calories",
    # 2026-08-11 batch (12 new + 3 corrections): Doug's continued field
    # census work in a separate session. Same direct on-device
    # verification standard as every other entry in this dict. Also
    # resolved: 23, 348, 349 were placeholder names built around the
    # "*"/"(Alt)" on-device marker before its meaning was confirmed --
    # renamed now that Doug verified their real on-device text directly
    # (see each entry below and the "*" marker note further down).
    2:   "Course Pt Dist.",
    3:   "Cadence",
    4:   "Avg Cadence",
    5:   "Lap Cadence",
    6:   "Distance",
    # 2026-08-10 batch (18 confirmed): the developer arranged two
    # screens to 10 fields each on a real profile specifically for this
    # census, entered/selected each field by its on-device name, then
    # cross-referenced every field's raw ID against its known on-screen
    # position using this toolkit's own GUI -- same direct verification
    # method as every other confirmed entry in this dict, just batched.
    7:   "Lap Dist.",
    9:   "Elevation (ft)",
    36:  "Power",
    37:  "Avg Power",
    38:  "Kilojoules",
    39:  "Lap Power",
    11:  "Percent Grade",
    12:  "Heading",
    13:  "Heart Rate",
    14:  "Avg Heart Rate",
    15:  "Lap HR",
    16:  "%Max Heart Rate",
    17:  "Avg %Max Heart Rate",
    18:  "Lap %Max HR",
    19:  "%Heart Rate Reserve",
    20:  "Avg %HRR",
    22:  "Heart Rate Zone",
    23:  "HR Zone Graph",  # CORRECTED 2026-08-11 -- was "Heart Rate (Alt)"; Doug verified the real on-device name directly, and it's a distinct Graph-type field, not literally an alternate view of plain Heart Rate
    27:  "Distance to Destination",
    28:  "Time to Destination",
    29:  "Distance to Next",
    30:  "Time to Next",
    31:  "Dest. Location",
    32:  "Next Pt Location",
    48:  "Speed",
    # 49: CORRECTED 2026-08-11 -- no record exists of how/why this was
    # originally named "Avg Speed (Alt)" (predates this project's
    # later discipline of noting confirmation method per field, same
    # blind spot that produced field 58's wrong "Lap Timer" guess).
    # Doug deployed it via the GUI into a full-width screen slot and
    # visually confirmed on-device: it's a plain text "Avg Speed"
    # value, no graph or bars. CAUTION for the Graph/Bars marker theory
    # (see 348/349's note): unlike 23/348/349, there's no record this
    # field's old "(Alt)" label was ever a literal transcription of an
    # on-device UI marker -- it may just have been an old, undocumented
    # guess that happened to reuse that word. Treat as a caution, not a
    # falsification: don't assume every OLD placeholder name containing
    # "(Alt)" reflects a real on-device marker unless that was actually
    # recorded at the time.
    49:  "Avg Speed",
    50:  "Lap Speed",
    53:  "Sunrise",
    54:  "Sunset",
    55:  "Elapsed Time",
    56:  "Timer",
    57:  "Avg Lap Time",
    # 58: found on a restored 8/3/2026 CyclingRoadSandbox backup
    # (surfaced by real GUI testing of Restore-from-Backup, v0.15.x --
    # not an active field-ID hunt), unrecognized by the GUI's field
    # picker at the time -- confirmed via direct visual comparison
    # against the live device display. CORRECTED 2026-08-11: originally
    # transcribed as "Lap Timer" (assumed by analogy to the separate,
    # correctly-named field 56 "Timer"), but a closer on-device
    # relabeling check found the real display text is "Lap Time" --
    # no "r". Field 56 "Timer" itself is unaffected and still correct.
    58:  "Lap Time",
    59:  "Time of Day (TOD)",
    60:  "Total Ascent",
    61:  "Total Descent",
    62:  "Dest. Ahead",
    63:  "Time Ahead",
    64:  "Calories to Go",
    65:  "Distance to Go",
    66:  "Heart Rate to Go",
    67:  "Reps to Go",
    68:  "Time to Go",
    77:  "VAM",
    78:  "Temperature",
    79:  "3s Power",
    81:  "Normalized Power",
    84:  "Last Lap Dist",
    86:  "Last Lap Speed",
    87:  "Last Lap Time",  # CORRECTED 2026-08-11 -- was "Last Lap Timer" (same "r" mixup as field 58, see its comment above)
    88:  "30s VAM",
    91:  "Max Speed",
    93:  "ETA at Destination",
    94:  "ETA to Next",
    95:  "Odometer",
    96:  "Battery Level",
    97:  "GPS Signal Strength",
    99:  "Aerobic Training Effect",
    146: "10s Power",
    165: "Last Lap HR",
    178: "Gears",
    179: "Front Gear",
    180: "Rear Gear",
    181: "Gear Battery",
    182: "Gear Ratio",
    199: "HR Zone 1 (time)",
    200: "HR Zone 2 (time)",
    201: "HR Zone 3 (time)",
    202: "HR Zone 4 (time)",
    203: "HR Zone 5 (time)",
    216: "CIQ Data Field",  # see CIQ_FIELD_MARKER_IDS below -- was
                            # "WindField Widget" until 2026-09-02; renamed
                            # generic once we confirmed this same numeric
                            # ID is reused by the DEVICE, not the app
    257: "Time Standing",
    259: "Time Seated",
    263: "Platform Center Offset",
    266: "Power Phase Right",
    270: "Avg R. Peak Pwr Phase",
    272: "Power Phase Left",
    276: "Avg L. Peak Pwr Phase",
    295: "Target Power",
    # 316/319: found on Gravel's Removed-state Slot 7, unresolved for
    # a long time (no on-device path to identify a Removed screen).
    # Confirmed via direct raw-ID injection test: patched a fresh slot
    # with exactly [316, 319] and visually confirmed on-device.
    316: "Lights Connected",
    319: "Light Mode",
    317: "Light Battery",  # Doug confirmed 2026-08-20: on-device, the Lights category also lists a "Battery Status" entry -- selecting it navigates straight to this SAME field (317), not a separate one. Alias/duplicate menu entry, not a distinct field -- no separate FIELD_ID_NAMES entry needed or added for "Battery Status".
    318: "Beam Angle Status",
    320: "Perf. Conditioning",  # CORRECTED 2026-08-11 -- was "Conditioning"; full concept name is "Performance Conditioning" but the actual on-device data field display reads "Perf. Conditioning" (abbreviated, matching this toolkit's convention of naming fields as they display on-device, e.g. "Lap Dist.", "Dest. Location")
    # 343/344/345/346/368: a Graph-type cluster, confirmed via TWO
    # independent screens (Tourtst Slot 0 [6-B layout] and Slot 16
    # [4-A layout]) plus on-ride photo verification. IMPORTANT: the
    # first pass at this cluster assumed raw field-array position
    # matched on-screen display position, which was WRONG for 344/346
    # -- corrected here after visually verifying on an actual ride
    # which graph was which. Lesson: don't assume array order = display
    # order, especially on B-variant (split) layouts.
    343: "Heart Rate Graph",
    344: "Speed Graph",
    345: "Cadence Graph",
    346: "Power Graph",
    347: "HR Bars",
    # 348/349: on Tourtst Slot 6 (nav-themed screen), visually read as
    # "Speed"/"Cadence" but marked with a "*" prefix in the on-device
    # editor -- NOT present on 48/3's normal Speed/Cadence fields (e.g.
    # Roadtest's Dashboard screen). Confirmed genuinely distinct from
    # 48/3 by this UI marker, not a duplicate or census row-slip.
    # MEANING RESOLVED 2026-08-11 (Doug verified directly): the "*"
    # marker denotes a Bars-type rendering -- Doug confirmed the real
    # on-device names are "Speed Bars"/"Cadence Bars", corrected below.
    # Same marker family as field 23 above (Graph-type) and the
    # standalone Bars entries 347/350 -- all need a full-width screen
    # slot to actually draw as a bar/graph, falling back to plain text
    # otherwise. See PROJECT_NOTES.md "Graph/Bars full-width warning"
    # (Open Items) for a scoped GUI feature to surface this to users.
    348: "Speed Bars",  # CORRECTED 2026-08-11 -- was "Speed *"
    349: "Cadence Bars",  # CORRECTED 2026-08-11 -- was "Cadence *"
    350: "Power Bars",
    368: "Elevation Graph",
    409: "Gear Combo",
    433: "Anaerobic TE",
    442: "Lap VAM",
    443: "Avg VAM",
    444: "Ascent Remaining",
    445: "Asc to Next Crs Pt",
    452: "Respiration",
    478: "EPOC",
    486: "Grit",
    487: "Lap Grit",
    488: "Flow",
    489: "Lap Flow",
    491: "Assist Mode",
    492: "Shifting Advice",
    493: "eBike Battery",
    494: "Travel Range",
    495: "60s Grit",
    497: "60s Flow",
    # 2026-08-17 batch, CORRECTED 2026-08-17 (same day): the original
    # 20-entry batch had the raw IDs and names correctly IDENTIFIED but
    # WRONGLY PAIRED -- Doug's own census screens 3 and 4 (Roadtemp
    # profile) got transposed when the list was written up, so every
    # ID from screen 4's block of 10 was paired with a NAME from screen
    # 3's block of 10 (and vice versa) -- a clean systematic offset,
    # not scattered individual errors: the SET of 20 raw IDs is
    # unchanged from the original batch, only which name each one
    # points to. Caught via real device testing: Doug edited Screen 4
    # (slot 7, CyclingRoadROAD.fit) using this toolkit to fields named
    # "Intensity Factor (IF)" (437)/"Pedal Smoothness" (147)/"Torque
    # Effect" (148)/"Perf. Conditioning" (320), but the profile
    # actually displays "Avg W/kg, Lap NP, Last Lap NP, Perf. Cond." on
    # the real device. Doug then re-derived the correct pairing
    # directly from Roadtemp's screen 3/4 field order and it resolves
    # ALL THREE mismatches exactly (437 -> Avg W/kg, 147 -> Lap NP, 148
    # -> Last Lap NP, matching the device precisely) while 320 stays
    # correctly "Perf. Conditioning" (unaffected, not part of this
    # batch). FULLY CONFIRMED 2026-08-17, same day: Doug's
    # CyclingRoadRoadtemp.fit (the original census profile itself --
    # slot 6 = Screen 3, slot 7 = Screen 4) came through on a second
    # upload attempt and was inspected directly via `fit_dump.py dump`.
    # Raw field-ID arrays: 14[6].7 = [150, 149, 177, 176, 43, 437, 40,
    # 408, 411, 441] (Screen 3), 14[7].7 = [80, 42, 148, 147, 82, 83,
    # 151, 161, 160, 159] (Screen 4) -- every single one of the 20
    # corrected (ID, name) pairs below matches these raw arrays
    # position-for-position exactly, including field 177 "Torque
    # Effect" under its own ID (closing the one residual flag this
    # batch was still carrying). Same direct byte-level verification
    # standard as every other confirmed batch in this dict.
    80:  "30s Power",
    42:  "%FTP",
    148: "Last Lap NP",
    147: "Lap NP",
    82:  "TSS",
    83:  "Intensity Factor (IF)",
    151: "Lap Balance",
    161: "30s Balance",
    160: "10s Balance",
    159: "3s Balance",
    150: "Avg Balance",
    149: "Balance",
    177: "Torque Effect",  # reported full concept name "Torque Effectiveness (Torque Effect.)" -- stored abbreviated, no trailing period, matching the on-device text confirmed for this field; CONFIRMED under this exact ID via direct raw-byte inspection of CyclingRoadRoadtemp.fit (see batch note above)
    176: "Pedal Smoothness",
    43:  "Power Zone",
    437: "Avg W/kg",
    40:  "Max Power",  # reported "MAX Power" -- normalized to Title Case to match this dict's existing "91: Max Speed" convention; not a factual correction, just consistent casing
    408: "Di2 Battery",
    411: "Di2 Shift Mode",
    441: "30s W/kg",
    # 2026-08-20 batch (9 new): Doug's continued field census, all 9
    # verified against the on-device screen -- same confirmation
    # standard as every other batch in this dict. No collisions with
    # any existing entry (confirmed via AST parse before insertion).
    # CORRECTION, same day: Doug caught his own transcription typo --
    # "Target" is field 521, not 512 (512 never existed on-device
    # under either name; simple mistyped digit, not a raw-ID/name
    # mismatch like the 2026-08-17 batch's screen-3/4 transposition).
    # Fixed before this ever shipped in a tagged release. Notable:
    # five of these (45, 511, 521, 522, 523) read as Workout/
    # structured-step fields by name (Workout Step, Workout
    # Comparison, Target, Duration, Step Time) -- directly adjacent to
    # this project's still-open f10=38 "Workout" SCREEN-TYPE question
    # (see FIELD_EDIT_UNCERTAIN_TYPES below and PROJECT_NOTES.md Open
    # Items): whether that screen's field slots are actually
    # meaningful/rendered, since the on-device editor exposes no field
    # options for it at all. That's a separate, still-unconfirmed
    # question from these 5 fields' own identity -- Doug's on-device
    # verification confirms the ID->name mapping itself with the same
    # confidence as any other entry here, it just doesn't by itself
    # establish whether/how these particular fields relate to f10=38.
    # The remaining 4 (100, 258, 260, 264) are unrelated additions to
    # already-populated families: Power (100, matching the existing
    # 3s/10s/30s/Lap/Avg pattern) and Cycling Dynamics (258/260/264,
    # alongside the existing standing/seated and PCO-adjacent entries).
    521: "Target",
    523: "Step Time",
    522: "Duration",
    511: "Workout Comparison",
    45:  "Workout Step",
    100: "Last Lap Power",
    258: "Lap Time Standing",
    260: "Lap Time Seated",
    264: "Avg PCO",
    # 2026-08-20 batch #2 (10 new): Doug's continued field census,
    # fills out the L/R Power Phase / Peak Power Phase family
    # alongside the existing 263/264 (PCO), 266/272 (instant Power
    # Phase Right/Left), 270/276 (Avg R./L. Peak Pwr Phase) entries --
    # this batch adds the missing Avg/Lap variants for both sides plus
    # the Right-side Peak Pwr Phase pair that had no entries at all
    # yet. Values below are the on-device DISPLAY labels (this dict's
    # established convention, matching "Perf. Conditioning"/"Lap
    # Dist." elsewhere) -- Doug also supplied each field's full
    # concept name for the record: 265 "Lap PCO" (Lap PCO, unabbreviated
    # already), 267 "Avg Right PP" (Avg Right Pwr Phase), 268 "Lap
    # Right PP" (Lap Right Pwr Phase), 269 "Right PPP" (Right Peak Pwr
    # Phase), 271 "Lap Right PPP" (Lap R. Peak Pwr Phase), 273 "Avg
    # Left PP" (Avg Left Pwr Phase), 274 "Lap Left PP" (Lap Left Pwr
    # Phase), 275 "Left PPP" (Left Peak Pwr Phase), 277 "Lap Left PPP"
    # (Lap L. Peak Pwr Phase). 440 "10s W/kg" (10s Watts/kg) extends
    # the existing 437/441 Avg/30s W/kg family the same way 79/146
    # already do for Power specifically. [CORRECTED 2026-08-20, this
    # comment only: originally said "159/441" for the pre-existing
    # W/kg family -- 159 is actually "3s Balance", an unrelated field;
    # the real pre-existing W/kg family was just 437/441.] No
    # collisions with any existing entry (confirmed via AST parse
    # before insertion).
    265: "Lap PCO",
    267: "Avg Right PP",
    268: "Lap Right PP",
    269: "Right PPP",
    271: "Lap Right PPP",
    273: "Avg Left PP",
    274: "Lap Left PP",
    275: "Left PPP",
    277: "Lap Left PPP",
    440: "10s W/kg",
    # 2026-08-20 batch #3 (13 new): Doug cross-checked his running
    # confirmed-field list against the Garmin Edge 530 Owner's
    # Manual's own data-field appendix, then went and located each
    # remaining gap on-device. Closes out that cross-check -- no
    # further appendix-listed fields remain unconfirmed as of this
    # batch. 98 "Watts/kg" and 439 "3s W/kg" (3s Watts/kg) fill the
    # last two gaps in the W/kg family (was 437/440/441 Avg/10s/30s
    # only, no base metric or 3s variant) -- now a complete mirror of
    # the Power family's own 36/79/146/80/37 base/3s/10s/30s/Avg
    # shape. 207-213/418/419 "Power Z1"-"Power Z9" (Time in Power
    # Zone 1-9) are the Power-Zone analog of the existing 199-203 "HR
    # Zone 1 (time)"-"HR Zone 5 (time)" fields -- notably 9 zones, not
    # 5, matching Garmin's documented 7-zone (classic) or Doug's own
    # zone-count-agnostic FTP-based setup allowing up to 9; on-device
    # DISPLAY label is the abbreviated "Power Z#" form (this dict's
    # established convention), full concept name "Time in Power Zone
    # #" noted here for the record. 24 "Laps" (a plain lap-count
    # field) and 41 "Max Lap Power" resolve what had been logged
    # ambiguously as "Laps Max" earlier this same day -- turned out to
    # be two separate fields Doug had conflated in his own notes, not
    # one field with an odd name; 41 extends the Power family's own
    # 39/40/100 Lap/Max/Last-Lap-Power set with the one remaining
    # combination. No collisions with any existing entry (confirmed
    # via AST parse before insertion). Trainer Resistance remains
    # UNCONFIRMED, not part of this batch -- working hypothesis
    # (unverified): may require a paired ANT+ FE-C smart trainer to
    # even appear in the on-device picker, the same sensor-gated
    # pattern already seen for eBike Metrics fields (f10=58's field
    # content, see the f10=38/58/95 "Corrections and lessons learned"
    # history) -- Doug doesn't currently have one to test against.
    98:  "Watts/kg",
    439: "3s W/kg",
    207: "Power Z1",
    208: "Power Z2",
    209: "Power Z3",
    210: "Power Z4",
    211: "Power Z5",
    212: "Power Z6",
    213: "Power Z7",
    418: "Power Z8",
    419: "Power Z9",
    24:  "Laps",
    41:  "Max Lap Power",
}

# Field IDs that MARK a screen position as holding a third-party
# Connect IQ data field.
#
# RENAMED in v2.6.0 from DEVICE_DEPENDENT_CIQ_IDS, because that name
# was wrong on both counts -- see PROJECT_NOTES.md Doc rev 106. The
# earlier understanding (Doc rev 95-97) was that 216 was a device-local,
# install-order-reassigned per-app identity, inferred from watching the
# same ID appear to mean a paid app ("WindField") and later a free one
# ("Edge 3270") on the same Edge 530. That inference was wrong.
#
# CONFIRMED (2026-09-06, Doug, real hardware) by placing BOTH apps on
# the SAME screen at adjacent positions simultaneously: both are stored
# as 216. The ID is a generic "a Connect IQ data field goes here"
# TYPE MARKER carrying no app identity whatsoever. What changed between
# the earlier observations was not the ID's meaning but the set of
# mesg_num=170 records around it. All app identity lives in those
# records -- each holds one app's UUID plus a packed list of the exact
# (screen slot, field position) pairs that app occupies. See
# fit_patch.py's read_ciq_records()/ciq_entry() for the format.
#
# This is general Connect IQ app-linking architecture, not a
# licensing/anti-piracy mechanism -- the free app behaves identically
# to the paid, license-keyed one.
#
# Deliberately a GROWABLE set: other devices or firmware may use a
# different marker ID. Add them here as found.
#
# The device renders Garmin's generic "Timer" fallback at any position
# holding this marker that no mesg 170 entry claims -- which is exactly
# what every pre-v1.3.0 toolkit write produced, since the toolkit
# rewrote field arrays without maintaining the records.
CIQ_FIELD_MARKER_IDS = {216}

# Backward-compatible alias for the pre-v2.6.0 name. Kept so any
# external script importing the old name keeps working; all in-repo
# callers use CIQ_FIELD_MARKER_IDS.
DEVICE_DEPENDENT_CIQ_IDS = CIQ_FIELD_MARKER_IDS

# Fields individually CONFIRMED on-device (2026-08-11, Doug) to render as
# a Graph or Bars widget, which only actually draws that way in a
# FULL-WIDTH screen slot -- placed in a shared/split row instead, it
# silently falls back to plain text with no on-device indication anything
# is wrong. Kept as its own set, separate from FIELD_ID_NAMES, so adding
# this category doesn't require touching every existing consumer of that
# dict. See PROJECT_NOTES.md "Graph/Bars full-width warning" (Open Items)
# for the full history of how this was confirmed, including field 49's
# important negative result: an OLD placeholder name merely containing
# "(Alt)" is NOT itself sufficient evidence -- 49 was checked directly
# on-device and turned out to be plain text, not Graph/Bars, despite its
# old "Avg Speed (Alt)" placeholder name superficially matching the same
# pattern as 23/348/349. This set only grows from fields where a real
# on-device marker (a "*"/"(Alt)" UI marker or a self-evidently-named
# Graph/Bars field) was directly observed and recorded at confirmation
# time. LIMITATION: false negatives are possible (an unflagged field that
# actually needs full width but hasn't been individually confirmed yet)
# but false positives should not be -- nothing here is a guess.
GRAPH_OR_BARS_FIELD_IDS = {
    23,   # HR Zone Graph
    343,  # Heart Rate Graph
    344,  # Speed Graph
    345,  # Cadence Graph
    346,  # Power Graph
    347,  # HR Bars
    348,  # Speed Bars
    349,  # Cadence Bars
    350,  # Power Bars
    368,  # Elevation Graph
}

# REMOVED (superseded below): previously had SYSTEM_SLOT_HINTS keyed by
# raw message_index (e.g. {8: "terminator", 10: "GroupTrack"}). CONFIRMED
# WRONG via a real profile (Indoor): slot numbers are NOT stable across
# profiles -- Slot 8 there is a genuine, populated 3-field screen, and
# Slot 10 is a genuine Cadence/Avg Cadence screen, neither remotely
# GroupTrack/terminator-like. That ruled out message_index (f 254) as an
# identity signal -- it's just a slot address, reused freely.
#
# CONFIRMED (side-thread Test 4, 2026-08-04): field 10 (f10), not slot
# number, is a genuine screen TYPE identifier -- global and content-
# independent. Two categories:
#   - Named Garmin screen types get a FIXED numeric code, the same value
#     regardless of profile/template or what content the user has since
#     customized the screen to show (proven: patched Cycling Dynamics'
#     fields via --force, redeployed -- f10 stayed 63, tag marks type,
#     not displayed content).
#   - Plain user-created screens use a per-profile, zero-indexed counter;
#     the on-device editor displays f10=N as "Screen N+1" (confirmed
#     exactly across 6 independent instances on one profile, no
#     exceptions).
# Named types are actively RE-APPLIED, not just inherited from original
# template creation: removing GroupTrack List on-device and re-adding it
# from the device's own named-screen menu brought it back tagged f10=57
# again, not the next free counter value. f9 (display order) and f10
# (identity) are fully independent -- removing a screen renumbers every
# other screen's f9 to close the gap, but f10 is untouched by that same
# operation.
#
# This is what finally makes "how many REAL user screens are left"
# answerable from the file alone -- see fit_patch.py's
# would_hide_last_visible_screen(). f10=32 and f10=57 were originally
# both assumed to be GroupTrack-related, but they're structurally
# independent: 32 is a Conditional-only runtime record (this module's
# "conditional" bucket, f9 absent) that has ALWAYS been present on
# every profile seen so far, active or not, regardless of whether
# GroupTrack has ever been used -- confirmed via an on-device
# remove-then-re-add of "GroupTrack List" (f10=57) alone, which left
# this f10=32 record completely unaffected either way. That
# always-present, content-independent behavior is a poor fit for a
# feature-specific record, and there's no direct confirmation this
# is GroupTrack's record at all rather than some other always-on
# system bookkeeping slot -- RENAMED from "GroupTrack" to "Reserved"
# (Doug's decision, 2026-08-15) to stop asserting an identity this
# project was never actually sure of. f10=57 ("GroupTrack List," the
# separate, always-orderable Active placeholder a user can add/remove
# from the on-device menu) is unaffected by this rename -- that one
# IS confirmed GroupTrack-specific, since it's the literal on-device
# menu entry for the feature.
NAMED_SCREEN_TYPES = {
    25:  "Map",
    26:  "Virtual Partner",
    32:  "Reserved",         # always-present Conditional-only runtime record of unclear purpose -- NOT confirmed GroupTrack-specific, see comment above (renamed from "GroupTrack" 2026-08-15)
    35:  "Compass",
    38:  "Workout",          # 2026-08-16 batch, CyclingEbike.fit -- raw f10, NOT the "Screen 39" label this displayed as before this entry existed (screen_type_name()'s f10+1 fallback: 38+1=39). See this file's own changelog: field bytes here are byte-for-byte IDENTICAL to slot 1's Cycling Dynamics (f10=63) record on this same profile, yet the on-device editor shows no fields/options for this type at all (Remove/Reorder only) -- CONFIRMED via direct raw dump comparison, not just field-name matching.
    44:  "Elevation",
    56:  "Segment",
    57:  "GroupTrack List",  # always-orderable Active placeholder, independent of the f10=32 record above -- this one IS the real GroupTrack menu entry
    58:  "eBike Metrics",    # 2026-08-16 batch, CyclingEbike.fit -- raw f10 (displayed as "Screen 59" before this entry existed, via the f10+1 fallback). e-bike-specific, first non-standard-Cycling profile this project has seen.
    63:  "Cycling Dynamics",
    74:  "Lap Summary",
    95:  "STEPS Metrics (Shimano)",  # 2026-08-16 batch, CyclingEbike.fit -- raw f10 (displayed as "Screen 96" before this entry existed, via the f10+1 fallback). Third-party drivetrain integration, first Shimano-branded screen type seen.
    104: "ClimbPro",
}

# Screen types whose stored field-slot bytes are real and correctly
# readable (unlike Map/GroupTrack List, which have a genuinely EMPTY
# field count -- see NAMED_SCREEN_TYPES above), but whose actual
# on-device meaning/rendering is uncertain -- editing them via this
# toolkit's EditScreenPanel may have no visible on-device effect at
# all. Currently just 38 "Workout": Doug confirmed the on-device
# screen editor shows NO field/option editing for this type (Remove/
# Reorder only), and a direct raw-byte comparison confirmed its field
# array is byte-for-byte IDENTICAL to Cycling Dynamics' (f10=63) own
# record on the same profile -- consistent with Garmin auto-stamping
# a shared default field template when creating certain system screen
# types, whether or not that type actually consumes fields at render
# time. Garmin's own Edge 530 manual (Training > Workouts) describes
# a SEPARATE structured-workout subsystem, independent of Activity
# Profile screens: starting a Workout "displays each step of the
# workout, the target (if any), and current workout data" -- almost
# certainly what this screen renders, dynamically, only while a
# Workout (Training > Workouts, synced via Garmin Connect or built
# on-device into GARMIN/Workouts/Guided or /Scheduled) is actively
# running, the same "only meaningful under a specific runtime
# condition" pattern already established for ClimbPro/Segment/
# GroupTrack. Doug's own device has never used this feature (both
# Workouts subfolders empty), matching why this screen has never been
# seen "live." NOT independently confirmed by this project via an
# actual running Workout -- inference from official Garmin
# documentation plus this profile's own byte-level evidence, not a
# direct on-device test of editing this screen's fields specifically.
#
# RESOLVED and EMPTIED 2026-09-10. Doug checked the on-device editor
# directly: "Workout" offers no editable data fields at all, so 38 was
# PROMOTED out of this warning set into NO_FIELD_EDIT_TYPES below --
# exactly the standard this project requires to turn a warning into a
# hard block. The set and its warning machinery (gui_app.py's
# field_edit_uncertain_warning_text()) are deliberately KEPT rather than
# deleted: this remains the right home for any future type whose field
# bytes are real and readable but whose on-device rendering is
# unverified, a situation that has arisen repeatedly here. Empty simply
# means no such type is currently known.
FIELD_EDIT_UNCERTAIN_TYPES = set()

# Screen types that hold NO user-editable data fields at all -- their
# whole content is generated by the device, so there is nothing for a
# field array to describe.
#
# 57 "GroupTrack List": Doug reported (2026-09-09) that selecting this
# screen in the GUI and pressing "Add Field..." opened the normal field
# picker, which it should not -- this screen renders a list of connected
# GroupTrack/LiveTrack riders, not data fields, and every profile this
# project has on hand carries it at f3=0 (no fields) without exception.
#
# 26 "Virtual Partner": added the same day after Doug checked the
# ON-DEVICE editor directly -- its screen-edit section offers no
# user-editable data fields and no preview-screen option, the same
# treatment GroupTrack List gets. That direct check is what promoted it
# from "likely, on file evidence" to a hard block; the file evidence
# alone was ambiguous, since Virtual Partner carries f3=255 (the uint8
# "unset" sentinel) rather than GroupTrack List's clean f3=0, and this
# project does not hard-block on an inference.
#
# DISTINCT from FIELD_EDIT_UNCERTAIN_TYPES above, which is a WARNING for
# types whose stored field bytes are real and readable but whose
# on-device rendering is unverified. This set is a HARD BLOCK: there is
# no field array to edit in the first place, so offering the controls is
# simply wrong rather than merely unproven. Enforced in fit_patch.py's
# CLI (any f3/f7/f8 write) and in gui_app.py's EditScreenPanel, which
# also greys the field controls out rather than only refusing on click.
#
# Deliberately a GROWABLE set, and the bar for adding to it is the same
# one NO_SHOW_TOGGLE_TYPES was held to: direct confirmation that the
# on-device editor offers no field options for the type. File evidence
# alone (an f3 of 0 or 255) is suggestive but not sufficient.
#
# 38 "Workout": added 2026-09-10, PROMOTED from FIELD_EDIT_UNCERTAIN_TYPES
# above after Doug confirmed on-device that it too offers no editable
# data fields. Worth noting what this settles: Workout carries f3=2 with
# a real, readable field array -- byte-for-byte identical to Cycling
# Dynamics' on the same profile -- and yet the device exposes no field
# editing for it. Taken with GroupTrack List (f3=0) and Virtual Partner
# (f3=255), that's three types with three DIFFERENT f3 values and the
# same "no editable fields" behaviour, which is conclusive that f3
# content cannot be used to infer this property. Only the on-device
# editor can.
NO_FIELD_EDIT_TYPES = {26, 38, 57}


# ----------------------------------------------------------------------
# ON-DEVICE LAYOUT GEOMETRY  (added v2.8.0, 2026-09-10)
# ----------------------------------------------------------------------
#
# This section is the SINGLE SOURCE for which field positions sit
# side-by-side vs. alone in a row, which (count, variant) states are
# legal, and where a named screen's device-generated content area sits.
#
# It is here, in fit_dump.py, on purpose. Before v1.4.0 this knowledge
# was SPLIT: gui_app.py owned LAYOUT_GRIDS (geometry for the diagram and
# the full-width advisories) while fit_patch.py owned
# COUNTS_WITH_B_VARIANT (which counts have a real A/B choice). Nothing
# forced those two to agree, and they drifted -- COUNTS_WITH_B_VARIANT
# listed 4 as having an A/B choice globally, which is true for ordinary
# user screens and WRONG for a 4-field Segment, whose "A" stores f8=2.
# Both modules now import from here.
#
# LAYOUT_GRIDS below is the ORDINARY USER SCREEN geometry, unchanged
# from gui_app.py v0.21.2 -- supplied from the developer's own
# text-based Edge 530 layout reference. Named screen types are a
# SEPARATE table (NAMED_SCREEN_LAYOUTS), because four things the code
# used to treat as global constants turn out to be per type:
#
#   LAYOUT_GRIDS          count -> rows        became  type + count -> rows
#   COUNTS_WITH_B_VARIANT {3,4,5,6,7}          became  per type
#   minimum field count   1, hardcoded         became  0 for Map/Segment
#   maximum field count   10                   became  fixed 2 for four types
#
# Counts 3 A vs B are visually the SAME row structure on the user-screen
# reference (B just renders the top field smaller) -- that size
# difference isn't representable by row/column grouping alone, so it is
# noted here rather than faked into the geometry.
LAYOUT_GRIDS = {
    1: {0: [[0]]},
    2: {0: [[0], [1]]},
    3: {
        0: [[0], [1], [2]],  # "A" -- equal sized fields
        1: [[0], [1], [2]],  # "B" -- same rows; on-device the TOP field renders smaller
    },
    4: {
        0: [[0], [1], [2], [3]],
        1: [[0, 1], [2], [3]],
    },
    5: {
        0: [[0], [1], [2], [3], [4]],
        1: [[0], [1], [2, 3], [4]],
    },
    6: {
        0: [[0], [1], [2], [3], [4, 5]],
        1: [[0, 1], [2], [3], [4, 5]],
    },
    7: {
        0: [[0], [1], [2], [3, 4], [5, 6]],
        1: [[0, 1], [2], [3, 4], [5, 6]],
    },
    8: {0: [[0], [1], [2, 3], [4, 5], [6, 7]]},
    9: {0: [[0], [1, 2], [3, 4], [5, 6], [7, 8]]},
    10: {0: [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]},
}

# Which ORDINARY-user-screen field counts offer a real A/B layout
# choice. Moved here from fit_patch.py v1.16.1 (which keeps a
# backward-compatible alias). Applies to plain user screens ONLY --
# a named type's A/B availability comes from its own 'states' list,
# because the VALUES differ (see NAMED_SCREEN_LAYOUTS).
COUNTS_WITH_B_VARIANT = {3, 4, 5, 6, 7}

# Flexible 1-4 named types (Lap Summary, eBike Metrics, STEPS Metrics)
# share one arrangement, measured on-device: 1 = one full width,
# 2 = two stacked full width, 3 = one full width on top plus two half
# width below, 4 = two rows of two half width. No A/B choice at any
# count -- the on-device selector offers a bare 1/2/3/4.
#
# POSITION 0 IS THE TOPMOST FIELD, and at count 4 the top-LEFT one.
# CONFIRMED on real hardware (Doug, 2026-09-10) by walking one field
# through all four counts on a Lap Summary screen -- the type whose
# content area sits at the BOTTOM, so the one where a bottom-up fill
# order was plausible and would have inverted every index here. With a
# single "Speed" field: at 2 it stays the top (full width) row; at 3 it
# stays that top full-width row while the two NEW fields become the
# half-width pair below it; at 4 it moves to the top-left half-width
# cell. So the stored array is top-to-bottom, left-to-right, identically
# to an ordinary user screen, and an existing field KEEPS its index when
# the count grows -- new fields are appended after it rather than pushing
# it along. That second half is what makes it safe for a layout change to
# grow a screen by appending (see gui_app.py's on_named_layout_choice()):
# the user's existing fields stay where they were.
_FLEX4_GRIDS = {1: [[0]], 2: [[0], [1]],
                3: [[0], [1, 2]], 4: [[0, 1], [2, 3]]}
_FLEX4_STATES = [(1, 0), (2, 0), (3, 0), (4, 0)]

# Per-type layout rules for Garmin's NAMED screens, from a complete
# on-device survey of all 12 named types (Doug, Edge 530,
# 2026-09-08 -> 2026-09-10). See PROJECT_NOTES.md Doc rev 112.
#
# 'states' holds the exact (field_count, f8_variant) pairs the on-device
# selector offers, IN THE ORDER IT OFFERS THEM. Every pair is MEASURED
# on real hardware, never derived -- which matters, because the obvious
# derivation is wrong. The working assumption for a long time was
# A=0 / B=1 universally. Segment's 4-field "A" actually stores f8=2,
# found only by saving 4/A, pulling the file, saving 4/B and pulling
# again: the two differed by exactly one byte plus the CRC, at mesg 14 /
# field 8. A single 4/B pull would have left the assumption intact and
# wrong. Hence: stored, never computed.
#
# 'grids' maps a field count to its row structure, same convention as
# LAYOUT_GRIDS above (a row holding two indices = two half-width fields
# side by side). An empty list means a legal ZERO-field layout, where
# the device-generated content fills the screen.
#
# 'content' is where that device-generated area sits relative to the
# data fields -- 'top' for every type except Lap Summary, whose fields
# sit ABOVE its lap table. Nothing is embedded in the content area that
# the profile stores: the selectable third column of Lap Summary's lap
# table ("Avg Speed" and friends) is NOT a data field and is not in the
# file at all, confirmed three ways (mesg-14 fields 5 and 6 are
# ff..ff/00..00 on every screen of every profile on hand, field id 49
# appears in no mesg-14 record, and a raw scan for 0x0031 hits only
# speed_zone in mesg 53). So a content area needs only a labelled block,
# with no embedded field index to track and no f7-ordering ambiguity.
#
# Types with NO editable fields (26 Virtual Partner, 38 Workout,
# 57 GroupTrack List) deliberately have NO entry here -- they are
# already fully handled by NO_FIELD_EDIT_TYPES above, and adding an
# empty-states entry would imply their field count is merely
# constrained rather than absent.
#
# Any f10 ABSENT from this table falls through to ordinary user-screen
# behaviour (LAYOUT_GRIDS + COUNTS_WITH_B_VARIANT), so plain screens are
# untouched by all of this, and a named type discovered on some future
# Edge model degrades to today's behaviour rather than erroring.
NAMED_SCREEN_LAYOUTS = {
    # --- one-offs -----------------------------------------------------
    # Map's two ZERO-field states are real and differ visibly: 0/B
    # devotes a larger share of the screen to the small elevation
    # graph that overlays the map. Confirmed by a paired pull.
    25: {'label': 'Map', 'content': 'top',
         'states': [(0, 0), (0, 1), (1, 0), (2, 0)],
         'grids': {0: [], 1: [[0]], 2: [[0, 1]]}},

    # Segment is the only type offering an EVEN-ONLY count (0/2/4/6,
    # no odd options at all) and the only one whose variant value is
    # neither 0 nor 1. Its elevation graphic shrinks or disappears
    # between 4/A and 4/B.
    56: {'label': 'Segment', 'content': 'top',
         'states': [(0, 0), (2, 0), (4, 2), (4, 1), (6, 0)],
         'grids': {0: [], 2: [[0, 1]], 4: [[0, 1], [2, 3]],
                   6: [[0, 1], [2, 3], [4, 5]]}},

    # --- fixed at 2 half-width, side by side --------------------------
    # The on-device editor offers NO count choice for these four: the
    # count is locked at 2, though field CONTENTS remain editable.
    # Writing 3 was tested on Compass and renders 2 (Speed, Distance),
    # clamped, with the file NOT rewritten -- see count_is_locked().
    35:  {'label': 'Compass', 'content': 'top',
          'states': [(2, 0)], 'grids': {2: [[0, 1]]}},
    44:  {'label': 'Elevation', 'content': 'top',
          'states': [(2, 0)], 'grids': {2: [[0, 1]]}},
    63:  {'label': 'Cycling Dynamics', 'content': 'top',
          'states': [(2, 0)], 'grids': {2: [[0, 1]]}},
    104: {'label': 'ClimbPro', 'content': 'top',
          'states': [(2, 0)], 'grids': {2: [[0, 1]]}},

    # --- flexible 1-4 -------------------------------------------------
    74: {'label': 'Lap Summary', 'content': 'bottom',   # fields ABOVE
         'states': _FLEX4_STATES, 'grids': _FLEX4_GRIDS},
    58: {'label': 'eBike Metrics', 'content': 'top',
         'states': _FLEX4_STATES, 'grids': _FLEX4_GRIDS},
    95: {'label': 'STEPS Metrics', 'content': 'top',
         'states': _FLEX4_STATES, 'grids': _FLEX4_GRIDS},
}

# Default field id stamped into a slot when a layout change GROWS a
# screen's field count and there is nothing to put there yet. 56
# "Timer" is chosen deliberately: it is the device's own universal
# fallback (what it renders for an unclaimed Connect IQ marker), it
# exists on every Edge model this project knows of, and it is
# unambiguous enough that a user seeing it knows it is a placeholder to
# change rather than a setting to interpret.
DEFAULT_FILLER_FIELD_ID = 56


def named_layout(f10):
    """
    The NAMED_SCREEN_LAYOUTS entry for this screen type, or None for an
    ordinary user screen (and for the no-editable-field types, which
    deliberately have no entry -- see NO_FIELD_EDIT_TYPES).
    """
    return NAMED_SCREEN_LAYOUTS.get(f10)


def layout_states(f10):
    """
    The (field_count, f8_variant) pairs this screen type can legally
    hold, in the order the on-device selector presents them.

    For an ordinary user screen (f10 not in NAMED_SCREEN_LAYOUTS) this
    is DERIVED from LAYOUT_GRIDS/COUNTS_WITH_B_VARIANT rather than
    measured, preserving today's behaviour exactly: every count in
    LAYOUT_GRIDS at variant 0, plus variant 1 for the counts in
    COUNTS_WITH_B_VARIANT.
    """
    entry = named_layout(f10)
    if entry is not None:
        return list(entry['states'])
    states = []
    for count in sorted(LAYOUT_GRIDS):
        states.append((count, 0))
        if count in COUNTS_WITH_B_VARIANT:
            states.append((count, 1))
    return states


def layout_grid(f10, count, variant=0):
    """
    Row structure for this type at this count -- a list of rows, each a
    list of 0-based field positions sharing that row. Two indices in one
    row means two half-width fields side by side.

    Returns [] for a legal zero-field layout (Map, Segment), and None
    when the combination isn't known at all, which callers must treat as
    "don't draw/advise" rather than as an error: a profile can legally
    hold a count this type cannot render (see layout_state_is_valid()).
    """
    entry = named_layout(f10)
    if entry is not None:
        return entry['grids'].get(count)
    return LAYOUT_GRIDS.get(count, {}).get(variant)


def layout_state_is_valid(f10, count, variant=0):
    """
    True if this exact (count, variant) is one the device offers for
    this screen type.

    False is NOT necessarily corruption. The device CLAMPS an
    over-range count when rendering (keeps the first N) and does NOT
    rewrite the file, so a profile can sit indefinitely holding a count
    larger than its type renders -- and Garmin's own on-device editor
    produces exactly this state too. Treat False as "flag it, read it as
    stored, change nothing", not as a reason to rewrite bytes the user
    didn't ask to touch.
    """
    return (count, variant) in layout_states(f10)


def layout_counts(f10):
    """Distinct field counts this screen type offers, ascending."""
    return sorted({count for count, _variant in layout_states(f10)})


def layout_variants_for_count(f10, count):
    """
    The f8 variant values legal at this count for this type, in the
    device's own order. Empty if the count itself isn't offered.

    Length > 1 is what "this count has an A/B choice" means -- asked
    per type and per count rather than against a global set of counts,
    because the VALUES are not positional: Segment at 4 returns
    [2, 1], so "A" is 2 and "B" is 1.
    """
    return [v for c, v in layout_states(f10) if c == count]


def layout_default_variant(f10, count):
    """
    The variant to store when a layout change lands on `count` and the
    caller has no explicit A/B preference -- the FIRST variant the
    on-device selector offers at that count, which is its "A".

    Returns None if the count isn't offered for this type. Never
    assumes 0: Segment at 4 correctly yields 2.
    """
    variants = layout_variants_for_count(f10, count)
    return variants[0] if variants else None


def count_is_locked(f10):
    """
    True if this screen type offers exactly ONE field count, so the
    count is not a user choice at all -- the four fixed-2 types
    (Compass, Elevation, Cycling Dynamics, ClimbPro).

    Field CONTENTS stay fully editable for these; only the count is
    fixed. Derived from 'states' rather than listed separately, so a
    type can never be locked and multi-count at the same time.
    """
    return len(layout_counts(f10)) == 1


def is_position_full_width(count, layout_variant, position, f10=None):
    """
    True if `position` (0-based) sits alone in its row for this field
    count and layout variant -- i.e. actually gets the full screen width
    on-device. False if it shares a row. None if the combination isn't
    known, which callers must treat as "no opinion" rather than as
    either answer.

    `f10` is OPTIONAL and trailing for backward compatibility, but
    passing it matters: without it every screen is measured against
    ordinary-user-screen geometry, where a 2-field layout is two STACKED
    FULL-WIDTH rows. On every fixed-2 named type the device instead
    renders two HALF-WIDTH fields side by side, so omitting f10 reports
    the exact opposite of the truth for those screens -- and since this
    function also feeds the Graph/Bars and Connect IQ half-width
    advisories, all three were wrong together before v1.4.0.
    """
    grid = layout_grid(f10, count, layout_variant) if f10 is not None \
        else LAYOUT_GRIDS.get(count, {}).get(layout_variant)
    if grid is None:
        return None
    for row in grid:
        if position in row:
            return len(row) == 1
    return None


def content_area_position(f10):
    """
    'top', 'bottom', or None -- where this named screen's
    device-generated content area (the map, the compass rose, the lap
    table) sits relative to its data fields. None for an ordinary user
    screen, which has no content area.

    Only Lap Summary (f10=74) returns 'bottom'. That one was measured
    from a device screenshot after this project had assumed 'top' for
    every named type.
    """
    entry = named_layout(f10)
    return entry['content'] if entry is not None else None


def screen_type_name(f10):
    """
    Human-readable screen TYPE name from field 10 (f10) -- NOT the
    screen's current field content (that can be freely customized, e.g.
    a "Map" screen showing Speed/Distance instead of a map overlay -- the
    type tag persists regardless), and NOT its display position (f9).

    Returns a known Garmin type name if f10 matches NAMED_SCREEN_TYPES,
    otherwise the on-device "Screen N" label a plain user-created screen
    actually shows (f10=N displays as "Screen N+1", confirmed exactly --
    see the NAMED_SCREEN_TYPES comment above). Returns None if f10 itself
    is absent -- e.g. a Removed-state screen has no real f10 to report.
    """
    if f10 is None:
        return None
    if f10 in NAMED_SCREEN_TYPES:
        return NAMED_SCREEN_TYPES[f10]
    return f"Screen {f10 + 1}"

# IDs seen in the wild but not yet identified with confidence.
# (84/87 RESOLVED 2026-08-04 -- see FIELD_ID_NAMES: Last Lap Dist/Last
# Lap Time (87 corrected 2026-08-11, was mistranscribed "Last Lap
# Timer"), confirmed via a forced-field test deployed successfully
# through NewFiles. Previously assumed GroupTrack-related purely by
# association with the f10=32 Conditional record they happened to be
# seen on -- they aren't GroupTrack-specific at all, just two ordinary
# lap-stat fields that record used them for other purposes.)
KNOWN_UNRESOLVED_IDS = set()


def _fmt_value(value):
    """Render a decoded field value as a single stable diff-friendly line."""
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    if isinstance(value, float):
        # Avoid float repr jitter across platforms; 6 sig figs is plenty
        # for anything a bike computer setting would encode.
        return f"{value:.6g}"
    return repr(value)


def _sort_key(k):
    # Message/field keys are either strings (known, named) or ints
    # (unknown, raw numeric id). Normalize to a tuple that sorts unknown
    # numeric ids after named ones, and sorts numerically within each group,
    # instead of raising a TypeError when Python tries to compare str to int.
    if isinstance(k, str):
        return (0, k, 0)
    return (1, "", k)


def decode_file(path):
    stream = Stream.from_file(path)
    decoder = Decoder(stream)
    messages, errors = decoder.read(
        apply_scale_and_offset=True,
        convert_datetimes_to_dates=False,   # keep raw epoch ints - more diffable
        convert_types_to_strings=True,      # enum names where the profile knows them
        expand_sub_fields=True,
        expand_components=True,
    )
    for err in errors:
        print(f"[decoder error] {path}: {err}", file=sys.stderr)
    return messages


def render_lines(messages):
    """Turn the messages dict into a flat, sorted list of diff-friendly lines."""
    lines = []
    for mesg_key in sorted(messages.keys(), key=_sort_key):
        occurrences = messages[mesg_key]
        for idx, mesg in enumerate(occurrences):
            for field_key in sorted(mesg.keys(), key=_sort_key):
                value = mesg[field_key]
                lines.append(
                    f"{mesg_key}[{idx}].{field_key} = {_fmt_value(value)}"
                )
    return lines


def is_unknown_mesg_key(k):
    # Known/named messages come back as strings from the SDK profile
    # (e.g. "record", "device_settings"). Unknown ones come back as the
    # raw numeric global_mesg_num, either as int or numeric-looking str.
    if isinstance(k, int):
        return True
    if isinstance(k, str) and k.isdigit():
        return True
    return False


def cmd_dump(args):
    messages = decode_file(args.file)
    for line in render_lines(messages):
        print(line)


def cmd_unknown(args):
    messages = decode_file(args.file)
    unknown = {k: v for k, v in messages.items() if is_unknown_mesg_key(k)}
    if not unknown:
        print("No undocumented (unknown global_mesg_num) messages found.",
              file=sys.stderr)
        return
    for line in render_lines(unknown):
        print(line)
    # Also flag unknown *fields* inside otherwise-known messages -- these
    # are numeric-keyed entries mixed in with named ones.
    print("\n--- unknown fields inside known messages ---", file=sys.stderr)
    for mesg_key, occurrences in messages.items():
        if is_unknown_mesg_key(mesg_key):
            continue
        for idx, mesg in enumerate(occurrences):
            for field_key in mesg.keys():
                if isinstance(field_key, int):
                    print(f"{mesg_key}[{idx}].{field_key} = "
                          f"{_fmt_value(mesg[field_key])}", file=sys.stderr)


def field_name(field_id, terse=False):
    """Return a display name for a field ID, or a clear unknown marker."""
    if field_id is None:
        return "--" if terse else "(empty slot)"
    if field_id in FIELD_ID_NAMES:
        return FIELD_ID_NAMES[field_id]
    if terse:
        return f"id{field_id}?"
    if field_id in KNOWN_UNRESOLVED_IDS:
        return f"UNKNOWN (id={field_id}, previously seen, unresolved)"
    return f"UNKNOWN (id={field_id}, NEW - not seen before)"


def active_field_ids(mesg, field_count):
    """
    Return just the ACTIVE field IDs for one data_screen message, given
    its field_count -- i.e. the meaningful prefix of field 7's 10-slot
    array, with the trailing leftover/sentinel entries dropped. Shared
    by the CLI printer (cmd_screens) and any other consumer (the GUI)
    that wants a screen's real field list without reimplementing this
    slicing logic itself. Pure function, no printing, no side effects.
    """
    raw_ids = mesg.get(7, [])
    return raw_ids[:field_count] if field_count else []


def classify_screens(messages):
    """
    Pure, print-free classification of a decoded FIT file's data_screen
    (mesg 14) occurrences into the three real on-device screen states
    (see SCREEN STATE MODEL in PROJECT_NOTES.md) plus never-configured
    slots. Safe to import and call directly -- e.g. from gui_app.py --
    with no subprocess call and no CLI output to parse back out.

    Returns a dict:
        {
            "orderable":        [(f9, idx, mesg), ...] sorted ascending
                                 by f9 -- this ordering IS the true
                                 on-device display order (confirmed via
                                 --swap-order round-trip testing).
            "conditional":      [(idx, mesg), ...] -- the always-present
                                 Conditional-only runtime record (f10=32,
                                 display name "Reserved" -- NOT confirmed
                                 GroupTrack-specific, see NAMED_SCREEN_TYPES'
                                 comment); active but exempt from f9 ordering.
            "removed":          [(idx, mesg), ...] -- soft-deleted; content
                                 (f3/f7) preserved ONLY until the next
                                 NewFiles-mediated (toolkit) deploy --
                                 NOT purged by on-device-only editing.
                                 See PROJECT_NOTES.md Screen State Model.
            "unconfigured":     [(idx, mesg), ...] -- no f1==1 signal at
                                 all (f9/f10 absent, f1 not 1), slot never
                                 created. NOTE (v2.3.0 bug fix): this is
                                 NOT gated on field 3 (f3) presence --
                                 some genuine Active screens (e.g. Virtual
                                 Partner, f10=26) have no f3 key at all.
            "unknown_ids_seen": set of field IDs present on this file
                                 that aren't in FIELD_ID_NAMES yet.
        }

    cmd_screens() below is just this function's CLI consumer -- it
    calls classify_screens() and then prints the result. The printed
    CLI output is unchanged by this split.
    """
    occurrences = messages.get(DATA_SCREEN_MESG_KEY, [])

    unknown_ids_seen = set()
    orderable = []    # (f9, slot_idx, mesg) -- real f9, appears in main viewing sequence
    conditional = []  # slot_idx, mesg -- f1=1, f9=None, f10=real (Conditional-state, still "on" -- historically called "GroupTrack-style," see the Reserved rename note above NAMED_SCREEN_TYPES)
    removed = []      # slot_idx, mesg -- f1=0, f9=None, f10=None (content preserved, pulled from sequence)
    unconfigured = [] # slot_idx, mesg -- no f1==1 signal at all (f9/f10 absent, f1 not 1) -- never created

    for m in occurrences:
        idx = m.get(254)
        # BUG FIX (v2.3.0, side-thread finding): field_count (f3) is NOT a
        # reliable configured/unconfigured gate -- some genuine, Active,
        # on-device screens (e.g. Virtual Partner, f10=26) have NO f3 key
        # at all, because they have no editable field list to begin with
        # (their displayed content is firmware-rendered, not read from f7).
        # Confirmed on live RoadClone data and in historical Indoor/
        # Mountain backups carrying the same f10=26 shape with no f3.
        # "Configured" now gates on f1/f9/f10 presence instead; field_count
        # defaults to 0 (not absent) when f3 is missing, which
        # active_field_ids() already treats correctly (falsy -> []).
        field_count = m.get(3)

        f1 = m.get(1)
        f9 = m.get(9)
        f10 = m.get(10)

        if f9 is not None:
            # Real, current display-order stamp -- Active/Display, on the
            # main scrollable sequence, regardless of whether f3 is present.
            orderable.append((f9, idx, m))
        elif f1 == 0:
            # CONFIRMED via live Remove-button test (see fit_patch.1 BUGS):
            # f1 0 + f9/f10 both absent = Removed. Field content (f3/f7)
            # is preserved untouched at the moment of removal -- but see
            # PROJECT_NOTES.md Screen State Model: this is only a soft
            # delete until the NEXT device write of any kind, not a
            # persistently stable state.
            removed.append((idx, m))
        elif f1 == 1 and f10 is not None:
            # f1 == 1, f9 absent, f10 present -- Conditional state: an
            # active record structurally exempt from the ordering system,
            # not a deleted screen. Always seen with f10=32 in practice --
            # display name "Reserved" (renamed 2026-08-15 from "GroupTrack,"
            # since this record is present on every profile regardless of
            # whether GroupTrack has ever been used, and its real purpose
            # isn't actually confirmed; distinct from the separate,
            # always-orderable "GroupTrack List" placeholder at f10=57,
            # which IS the real GroupTrack menu entry).
            conditional.append((idx, m))
        else:
            # No f1==1 signal of any kind (f9 absent, f10 absent, f1 not 1)
            # -- genuinely never-created slot, available for --new-slot.
            unconfigured.append((idx, m))
            continue

        active_ids = active_field_ids(m, field_count)
        for fid in active_ids:
            if fid is not None and fid not in FIELD_ID_NAMES:
                unknown_ids_seen.add(fid)

    # Sort by f9 ascending -- CONFIRMED to match real on-device display
    # order (validated against the developer's Gravel profile editor
    # sequence, and against an actual --swap-order device round-trip
    # test). This is what a person sees scrolling through the Active
    # Profile, NOT the raw slot/message_index order.
    orderable.sort(key=lambda t: t[0])

    return {
        "orderable": orderable,
        "conditional": conditional,
        "removed": removed,
        "unconfigured": unconfigured,
        "unknown_ids_seen": unknown_ids_seen,
    }


def cmd_screens(args):
    """
    CLI entry point for `fit_screens.py screens`. Unchanged output from
    prior versions -- this is now just classify_screens() plus the same
    printing logic that used to be inlined here directly.
    """
    messages = decode_file(args.file)
    data = classify_screens(messages)
    verbose = args.verbose

    orderable = data["orderable"]
    conditional = data["conditional"]
    removed = data["removed"]
    unconfigured = data["unconfigured"]
    unknown_ids_seen = data["unknown_ids_seen"]

    def _row(idx, m, field_count, position=None):
        # v2.3.0: field_count can genuinely be None now (Virtual
        # Partner-style screens have no f3 key at all) -- default to 0
        # for display/formatting purposes only.
        field_count = field_count or 0
        active_ids = active_field_ids(m, field_count)
        names = ", ".join(field_name(fid, terse=not verbose) for fid in active_ids)

        layout_variant = m.get(8)
        if verbose:
            if layout_variant == 1:
                layout_col = "B/alternate"
            elif layout_variant == 0:
                layout_col = "A/default"
            elif layout_variant is not None:
                layout_col = f"variant={layout_variant}?"
            else:
                layout_col = "-"
        else:
            layout_col = "B" if layout_variant == 1 else " "

        enabled = m.get(12)
        flag = "OFF" if enabled == 1 else "   "

        # v2.3.0: real screen-type name from f10 -- see NAMED_SCREEN_TYPES.
        type_name = screen_type_name(m.get(10)) or "?"

        pos_col = f"{position:3d}" if position is not None else "  -"
        if verbose:
            line = (f"  {pos_col}  slot {idx:2d}  {field_count:2d}f  {layout_col:11s}  "
                    f"{flag}  {type_name:16s} [{names}]")
        else:
            line = (f"  {pos_col}  [{idx:2d}]  {field_count:2d}f {layout_col} {flag}  "
                    f"{type_name:16s} {names}")
        return line

    print("=== Screen order as viewed on-device (reorderable via --swap-order) ===")
    if verbose:
        print("  POS  SLOT      CNT  LAYOUT       FLAG  TYPE              FIELDS")
    else:
        print("  POS  SLOT  CNT LAY FLAG  TYPE              FIELDS")
    for position, (f9, idx, m) in enumerate(orderable, start=1):
        field_count = m.get(3)
        print(_row(idx, m, field_count, position))

    if conditional:
        print()
        print("=== Conditional screens (active record, exempt from normal ordering -- "
              "always seen as f10=32 'Reserved'; --swap-order refuses these, no f9 to swap) ===")
        for idx, m in conditional:
            field_count = m.get(3)
            print(_row(idx, m, field_count))
        if verbose:
            print("  NOTE: this section catches the Conditional-state structural exemption "
                  "(f1=1, f9 absent, f10 present). Other conditionally-TRIGGERED screens "
                  "(e.g. ClimbPro) may still have a real f9 and appear in the main ordered "
                  "list above instead -- they participate normally in scroll order even "
                  "though their content is only 'live' under specific circumstances. Not "
                  "all conditional features work the same way structurally.")

    if removed:
        print()
        print("=== Removed screens (content preserved, pulled from the display sequence) ===")
        for idx, m in removed:
            field_count = m.get(3)
            print(_row(idx, m, field_count))
        if verbose:
            print("  NOTE: confirmed via live Remove-button test; NOT restorable via any "
                  "on-device menu, and fit_patch.py no longer offers an --un-remove flag "
                  "either (RETIRED v1.13.0, 2026-08-13) -- it had a real, confirmed "
                  "device-side data-loss hazard in earlier testing and was never re-verified "
                  "after the fix, and Garmin's own editor has no un-remove workflow at all. "
                  "Recovery from an unwanted change is Restore-from-Backup (whole profile), "
                  "not a per-screen undo -- see FIT_PATCH.md BUGS / PROJECT_NOTES.md "
                  "\"Product note on --un-remove\" for the full history.")

    if args.show_unconfigured and unconfigured:
        print()
        print("=== Unconfigured (never created, available for --new-slot) ===")
        for idx, m in unconfigured:
            print(f"  [slot {idx:2d}]")

    total_configured = len(orderable) + len(conditional) + len(removed)
    print()
    print(f"  ({total_configured} configured screen slot(s) total: "
          f"{len(orderable)} reorderable, {len(conditional)} conditional, "
          f"{len(removed)} removed)", file=sys.stderr)
    if unknown_ids_seen:
        if verbose:
            print(f"  ** unknown field IDs on this file: {sorted(unknown_ids_seen)}",
                  file=sys.stderr)
        else:
            print(f"  ** unknown field IDs on this file: {sorted(unknown_ids_seen)} "
                  f"(run with -v for detail)", file=sys.stderr)


def cmd_diff(args):
    import difflib
    a_lines = render_lines(decode_file(args.file_a))
    b_lines = render_lines(decode_file(args.file_b))
    diff = difflib.unified_diff(
        a_lines, b_lines,
        fromfile=args.file_a, tofile=args.file_b,
        lineterm="",
    )
    had_output = False
    for line in diff:
        had_output = True
        print(line)
    if not had_output:
        print("No differences.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_dump = sub.add_parser("dump", help="Dump one FIT file as sorted, diff-friendly text")
    p_dump.add_argument("file")
    p_dump.set_defaults(func=cmd_dump)

    p_unknown = sub.add_parser("unknown", help="Show only messages/fields not in the public FIT profile")
    p_unknown.add_argument("file")
    p_unknown.set_defaults(func=cmd_unknown)

    p_screens = sub.add_parser("screens", help="Human-readable data_screen (mesg 14) report: "
                                                 "screen index, field count, field names")
    p_screens.add_argument("file")
    p_screens.add_argument("--all", dest="show_unconfigured", action="store_true",
                            help="Also list unconfigured/preallocated-but-empty screen slots")
    p_screens.add_argument("-v", "--verbose", action="store_true",
                            help="Full detail: long unknown-field text, full system-slot "
                                 "explanations, full layout labels. Default is a compact, "
                                 "column-aligned view.")
    p_screens.set_defaults(func=cmd_screens)

    p_diff = sub.add_parser("diff", help="Decode two FIT files and diff them directly")
    p_diff.add_argument("file_a")
    p_diff.add_argument("file_b")
    p_diff.set_defaults(func=cmd_diff)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
