import { execFileSync } from "node:child_process";
import path from "node:path";

import { USERS_FILE } from "./global-setup";

export default function globalTeardown() {
  execFileSync("uv", ["run", "python", "scripts/e2e_users.py", "teardown", USERS_FILE], {
    cwd: path.resolve(__dirname, "../../../backend"),
    stdio: "inherit",
  });
}
