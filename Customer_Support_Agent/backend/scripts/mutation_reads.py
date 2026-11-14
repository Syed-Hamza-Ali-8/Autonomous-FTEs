"""Mutation check for tests/test_read_isolation.py: each SQL ownership filter, removed, must break a test.

The parameter stays referenced (`$n::text IS NOT NULL`), so a test fails because data leaks,
not because the query errors.
Usage (from backend/, with `supabase start` running):  uv run python -m scripts.mutation_reads
"""

import sys

from scripts.mutation_lib import CodeMutation, run_suite

F = "tollgate/domain/orders.py"
T = "tests/test_read_isolation.py::"

MUTATIONS = (
    CodeMutation(
        "list_orders_unfiltered",
        "list_orders filters by customer in SQL",
        F,
        "         WHERE o.customer_id = $1 AND ($2::text IS NULL OR o.status = $2)\n",
        "         WHERE ($1::text IS NOT NULL) AND ($2::text IS NULL OR o.status = $2)\n",
        (T + "test_list_orders_returns_only_own_orders", T + "test_get_my_orders_lists_only_own"),
    ),
    CodeMutation(
        "get_order_unfiltered",
        "get_order loads the order WHERE id AND customer_id",
        F,
        "         WHERE id = $1 AND customer_id = $2\n",
        "         WHERE id = $1 AND ($2::text IS NOT NULL)\n",
        (
            T + "test_get_order_of_other_customer_is_none",
            T + "test_foreign_missing_and_malformed_orders_look_identical",
        ),
    ),
    CodeMutation(
        "get_shipment_unfiltered",
        "get_shipment joins orders and filters by customer",
        F,
        "         WHERE s.order_id = $1 AND o.customer_id = $2\n",
        "         WHERE s.order_id = $1 AND ($2::text IS NOT NULL)\n",
        (T + "test_get_order_of_other_customer_is_none",),
    ),
    CodeMutation(
        "refund_history_unfiltered",
        "get_refund_history checks ownership in SQL",
        F,
        '"SELECT 1 FROM app.orders WHERE id = $1 AND customer_id = $2"',
        '"SELECT 1 FROM app.orders WHERE id = $1 AND ($2::text IS NOT NULL)"',
        (T + "test_get_order_of_other_customer_is_none",),
    ),
)

if __name__ == "__main__":
    sys.exit(run_suite("reads", "tests/test_read_isolation.py", MUTATIONS))
