"""Mutation check for tests/test_auth_tokens.py: each verifier check, removed, must break its test.

Usage (from backend/, with `supabase start` running):  uv run python scripts/mutation_auth.py
"""

import sys

from scripts.mutation_lib import CodeMutation, run_suite

F = "tollgate/auth/supabase_jwt.py"
T = "tests/test_auth_tokens.py::"

MUTATIONS = (
    CodeMutation(
        "no_alg_allowlist",
        "header alg checked against the allowlist",
        F,
        "        if alg not in self._algorithms:\n",
        "        if False:\n",
        (
            T + "test_alg_none_is_rejected",
            T + "test_hs256_with_any_secret_is_rejected",
            T + "test_anon_key_presented_as_token_is_rejected",
        ),
    ),
    CodeMutation(
        "no_required_claims",
        "exp/iat/sub/aud/iss must be present",
        F,
        'options={"require": REQUIRED_CLAIMS},',
        "options={},",
        (T + "test_token_missing_required_claim_is_rejected",),
    ),
    CodeMutation(
        "no_expiry_check",
        "exp is verified",
        F,
        'options={"require": REQUIRED_CLAIMS},',
        'options={"require": REQUIRED_CLAIMS, "verify_exp": False},',
        (T + "test_expired_token_is_rejected",),
    ),
    CodeMutation(
        "no_audience_check",
        "aud must be 'authenticated'",
        F,
        'options={"require": REQUIRED_CLAIMS},',
        'options={"require": REQUIRED_CLAIMS, "verify_aud": False},',
        (T + "test_wrong_audience_is_rejected",),
    ),
    CodeMutation(
        "no_issuer_check",
        "iss must be this project's Auth URL",
        F,
        "                issuer=self._s.issuer,\n",
        "                issuer=None,\n",
        (T + "test_wrong_issuer_is_rejected",),
    ),
    CodeMutation(
        "no_kid_alg_binding",
        "a kid's algorithm must match the token's alg",
        F,
        "        if key.algorithm_name != alg:\n",
        "        if False:\n",
        (T + "test_kid_algorithm_mismatch_is_rejected",),
    ),
    CodeMutation(
        "no_uuid_subject",
        "sub must be a UUID",
        F,
        '            sub = uuid.UUID(str(claims["sub"]))\n',
        '            sub = uuid.UUID(int=0) if not str(claims["sub"]) else uuid.UUID(int=1)\n',
        (T + "test_non_uuid_subject_is_rejected",),
    ),
    CodeMutation(
        "jwks_fail_open",
        "an unreachable JWKS fails closed",
        F,
        '            raise AuthUnavailableError(f"cannot load JWKS: {type(exc).__name__}") from exc\n',
        "            return\n",
        (T + "test_unreachable_jwks_fails_closed",),
    ),
)

if __name__ == "__main__":
    sys.exit(run_suite("auth", "tests/test_auth_tokens.py", MUTATIONS))
