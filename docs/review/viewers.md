# PDF viewer qualification packet

**Status: pending per viewer/version and final PDF.** Rendering with the engine
is useful but does not replace interactive checks in the viewer being claimed.

Record OS, viewer name/version, source and final PDF SHA256, target locale and
font identifiers. Use invented text and a copy of the finalized PDF for editing;
never change the immutable delivery during a test.

1. Open the exact final PDF. Check every page at normal and enlarged zoom for
   clipping, missing glyphs, rotated text, lines, lists and field appearance.
2. Enter target-language text in each field class. Include letters outside ASCII
   and shaped-script text when in scope. Exercise tab order, checkboxes, radio
   groups, combo boxes and list selections present in the source.
3. Save the edited test copy, close the viewer, reopen it and confirm values and
   appearance persist. Verify choice display labels and underlying export values
   remain appropriate. Check inherited and rotated fields if claiming them.
4. Exercise links/bookmarks and print preview only as permitted by the task.
   Do not activate unexpected external links or active content as a side effect.
5. Record exact failures and untested field types. Bind the viewer assessment to
   the unedited final PDF hash, with edited-copy evidence separately identified.

Adobe startup failure, an unavailable app, browser URL-policy refusal or an
inaccessible native UI means **blocked/not performed**, not viewer pass or PDF
failure. Do not bypass those restrictions to produce a compatibility claim.

Use the `viewer` category of the review record only after actual checks. Use
`visual` separately for page inspection and leave `accessibility` unperformed
unless an appropriate assistive-technology assessment was conducted.
