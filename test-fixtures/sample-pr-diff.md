# Sample PR Diff

```diff
diff --git a/src/profile.ts b/src/profile.ts
@@
-export function normalizeName(name: string) {
-  return name.trim();
-}
+export function normalizeName(name: string | null) {
+  return name.trim();
+}
```

Review focus:

- Null handling
- Regression test coverage
- TASK_SPEC alignment
