# Sample Bug Report

The settings page crashes when the API returns `null` for `displayName`.

Observed:

- Error: `TypeError: Cannot read properties of null`
- Expected: show a fallback empty input value and allow the user to save a valid name.
