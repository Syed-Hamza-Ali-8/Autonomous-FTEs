// Mutation check for tests/e2e/isolation.spec.ts (Rule 0.1.11): remove the cache protections and
// require the isolation test to FAIL. Files are restored in `finally` and verified by hash.
//
// Required:  both layers removed (user-scoped keys AND cache clearing) -> the test must fail.
// Recorded:  each layer removed alone -> shows whether the other layer still holds (defence in depth).
//
// Usage (from frontend/, with `supabase start` running):  node scripts/mutation-isolation.mjs
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import fs from "node:fs";

const QUERIES = "src/lib/queries.ts";
const AUTH = "src/lib/auth.tsx";

const unscopeKeys = { file: QUERIES, from: /queryKey: \[userId, /g, to: "queryKey: [" };
const noClear = { file: AUTH, from: /queryClient\.clear\(\);/g, to: "/* mutated: no clear */" };

const MUTATIONS = [
  { name: "no_user_keys_and_no_clear", required: true, edits: [unscopeKeys, noClear] },
  { name: "no_clear_only", required: false, edits: [noClear] },
  { name: "no_user_keys_only", required: false, edits: [unscopeKeys] },
];

const sha = (p) => createHash("sha256").update(fs.readFileSync(p)).digest("hex");
const runIsolation = () => {
  const r = spawnSync("npx", ["playwright", "test", "--project=isolation", "--reporter=line"], { encoding: "utf8" });
  const lines = (r.stdout + r.stderr).split("\n").filter((l) => !l.includes("[WebServer]"));
  const why = lines.filter((l) => /Error:|Expected|Received|appeared|passed|failed/.test(l)).slice(0, 8);
  return { failed: r.status !== 0, tail: why.join("\n").trim() };
};

const results = [];
const baseline = runIsolation();
console.log(`baseline: ${baseline.failed ? "FAIL" : "PASS"}`);
if (baseline.failed) process.exit(1);

for (const m of MUTATIONS) {
  const originals = new Map(m.edits.map((e) => [e.file, fs.readFileSync(e.file)]));
  const hashes = new Map([...originals.keys()].map((f) => [f, sha(f)]));
  let outcome;
  try {
    for (const e of m.edits) {
      const text = fs.readFileSync(e.file, "utf8");
      const next = text.replace(e.from, e.to);
      if (next === text) throw new Error(`${m.name}: pattern not found in ${e.file}`);
      fs.writeFileSync(e.file, next);
    }
    outcome = runIsolation();
  } finally {
    for (const [f, data] of originals) fs.writeFileSync(f, data);
  }
  for (const [f, h] of hashes) if (sha(f) !== h) throw new Error(`FATAL: ${f} not restored`);
  const verdict = outcome.failed ? "CAUGHT (test failed)" : "not caught (test passed)";
  console.log(`${m.name}${m.required ? "" : " [info]"}: ${verdict}`);
  results.push({ ...m, edits: m.edits.map((e) => e.file), failed: outcome.failed, tail: outcome.tail });
}

const after = runIsolation();
console.log(`baseline after: ${after.failed ? "FAIL" : "PASS"}`);
const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
fs.mkdirSync("../backend/eval/runs/mutation", { recursive: true });
fs.writeFileSync(
  `../backend/eval/runs/mutation/isolation-e2e-${stamp}.json`,
  JSON.stringify({ baseline_before: !baseline.failed, baseline_after: !after.failed, mutations: results }, null, 2) + "\n",
);
const ok = !after.failed && results.filter((r) => r.required).every((r) => r.failed);
process.exit(ok ? 0 : 1);
