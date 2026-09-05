# macOS qualification packet

**Status: pending; no actual Mac qualification is asserted.** Test on a real
Mac and record macOS version, architecture, Python executable/version, resolved
dependencies, preview manifest hash and agent host/version.

1. Follow [installation](../INSTALL.md) in a fresh venv using the source-only
   preview. Verify the manifest and generate the synthetic example locally.
2. Run the complete workflow on the sample, including an authored mapping,
   licensed font coverage, rebuild, finish and independent manifest validation.
   Record every command result; do not treat an unattempted finish as passed.
3. Check every finalized page and perform the [viewer protocol](viewers.md)
   in Preview.app and any other viewer being claimed. Name exact versions.
4. Include a shaped-script form case if claiming shaped-script behavior.
   Confirm logical extraction as well as visual joining and form entry.
5. Record pass/fail/not-performed for each check. Retain failures and repeat
   affected checks after any fix using new output filenames and hashes.

A successful import or CLI help screen is installation evidence only. A Preview
render is not evidence of Acrobat editing, and an Apple Silicon run does not
qualify Intel hardware. Do not infer human translation or accessibility review.
Publish only consented synthetic summaries; keep raw local paths and logs private.
