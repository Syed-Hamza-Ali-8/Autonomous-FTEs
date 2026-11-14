import { execFileSync } from "node:child_process";
import path from "node:path";

export const USERS_FILE = path.resolve(__dirname, ".auth/users.json");

export default function globalSetup() {
  execFileSync("uv", ["run", "python", "scripts/e2e_users.py", "create", USERS_FILE], {
    cwd: path.resolve(__dirname, "../../../backend"),
    stdio: "inherit",
  });
}
