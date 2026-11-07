-- Northwind Goods store data (spec Section 4.2; DECISIONS A2, E1, E2).
--
-- Conventions for every table in app (enforced by tests/test_supabase_lockdown.py):
--   ENABLE ROW LEVEL SECURITY (no policies) and REVOKE ALL ON TYPE <row type> FROM PUBLIC.
-- Money columns ending in _cents hold integer minor units of the row's currency (PKR = paisa).
-- Composite (id, currency) keys make the DB reject an item, payment or refund whose currency
-- differs from its order's (E2).

-- customers -------------------------------------------------------------------------------------
CREATE TABLE app.customers (
  id            text PRIMARY KEY CHECK (id ~ '^CUS-[0-9]{3}$'),
  auth_user_id  uuid UNIQUE REFERENCES auth.users (id) ON DELETE SET NULL,  -- NULL for seed-only customers
  email         text NOT NULL UNIQUE CHECK (email = lower(email)),
  name          text NOT NULL,
  tier          text NOT NULL DEFAULT 'standard' CHECK (tier IN ('standard', 'gold')),
  created_at    timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE app.customers ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.customers FROM PUBLIC;

-- products: one row per currency (regional SKU) -------------------------------------------------
CREATE TABLE app.products (
  id           text PRIMARY KEY CHECK (id ~ '^PRD-[0-9]{3}$'),
  name         text NOT NULL,
  category     text NOT NULL CHECK (category IN ('electronics', 'home', 'apparel')),
  final_sale   boolean NOT NULL DEFAULT false,
  digital      boolean NOT NULL DEFAULT false,
  currency     text NOT NULL CHECK (currency IN ('USD', 'PKR')),
  price_cents  integer NOT NULL CHECK (price_cents >= 0),
  UNIQUE (id, currency)
);
ALTER TABLE app.products ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.products FROM PUBLIC;

-- orders ----------------------------------------------------------------------------------------
CREATE TABLE app.orders (
  id                text PRIMARY KEY CHECK (id ~ '^ORD-[0-9]{4}$'),
  customer_id       text NOT NULL REFERENCES app.customers (id),
  status            text NOT NULL CHECK (status IN ('pending', 'paid', 'packed', 'shipped', 'delivered',
                                                    'cancelled', 'refunded', 'partially_refunded')),
  currency          text NOT NULL CHECK (currency IN ('USD', 'PKR')),
  total_cents       integer NOT NULL CHECK (total_cents >= 0),
  shipping_address  jsonb NOT NULL CHECK (jsonb_typeof(shipping_address) = 'object'),
  notes             text,  -- free text; fixtures plant injection payloads here (data, never instructions)
  placed_at         timestamptz NOT NULL,
  paid_at           timestamptz,
  packed_at         timestamptz,
  delivered_at      timestamptz,
  UNIQUE (id, currency),
  CHECK (paid_at IS NULL OR paid_at >= placed_at),
  CHECK (packed_at IS NULL OR packed_at >= coalesce(paid_at, placed_at)),
  CHECK (delivered_at IS NULL OR delivered_at >= placed_at)
);
CREATE INDEX orders_customer_id_idx ON app.orders (customer_id, placed_at DESC);
ALTER TABLE app.orders ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.orders FROM PUBLIC;

-- order_items -----------------------------------------------------------------------------------
CREATE TABLE app.order_items (
  id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_id          text NOT NULL,
  product_id        text NOT NULL,
  currency          text NOT NULL,
  quantity          integer NOT NULL CHECK (quantity > 0),
  unit_price_cents  integer NOT NULL CHECK (unit_price_cents >= 0),  -- price paid; recompute source
  downloaded_at     timestamptz,                                      -- digital goods only (B1)
  FOREIGN KEY (order_id, currency) REFERENCES app.orders (id, currency),
  FOREIGN KEY (product_id, currency) REFERENCES app.products (id, currency)
);
CREATE INDEX order_items_order_id_idx ON app.order_items (order_id);
ALTER TABLE app.order_items ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.order_items FROM PUBLIC;

-- payments: append-only captured payments -------------------------------------------------------
CREATE TABLE app.payments (
  id            text PRIMARY KEY CHECK (id ~ '^PAY-[0-9]{4,}$'),
  order_id      text NOT NULL,
  currency      text NOT NULL,
  amount_cents  integer NOT NULL CHECK (amount_cents > 0),
  captured_at   timestamptz NOT NULL,
  FOREIGN KEY (order_id, currency) REFERENCES app.orders (id, currency)
);
CREATE INDEX payments_order_id_idx ON app.payments (order_id);
ALTER TABLE app.payments ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.payments FROM PUBLIC;

-- shipments -------------------------------------------------------------------------------------
CREATE TABLE app.shipments (
  id               text PRIMARY KEY CHECK (id ~ '^SHP-[0-9]{4,}$'),
  order_id         text NOT NULL UNIQUE REFERENCES app.orders (id),
  carrier          text NOT NULL,
  tracking_number  text NOT NULL,
  status           text NOT NULL CHECK (status IN ('label_created', 'in_transit', 'out_for_delivery', 'delivered')),
  events           jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(events) = 'array'),
  shipped_at       timestamptz,
  delivered_at     timestamptz
);
ALTER TABLE app.shipments ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.shipments FROM PUBLIC;

-- product_reviews: fixtures plant injection payloads in body ------------------------------------
CREATE TABLE app.product_reviews (
  id           text PRIMARY KEY CHECK (id ~ '^REV-[0-9]{3,}$'),
  product_id   text NOT NULL REFERENCES app.products (id),
  customer_id  text NOT NULL REFERENCES app.customers (id),
  rating       integer NOT NULL CHECK (rating BETWEEN 1 AND 5),
  body         text NOT NULL,
  created_at   timestamptz NOT NULL
);
ALTER TABLE app.product_reviews ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.product_reviews FROM PUBLIC;

-- refunds (E1): historical rows from the seed now; action rows from Phase 3 ---------------------
CREATE TABLE app.refunds (
  id                 text PRIMARY KEY CHECK (id ~ '^REF-[0-9]{4,}$'),
  order_id           text NOT NULL,
  currency           text NOT NULL,
  amount_cents       integer NOT NULL CHECK (amount_cents > 0),
  status             text NOT NULL CHECK (status IN ('pending_approval', 'succeeded', 'rejected')),
  source             text NOT NULL CHECK (source IN ('historical', 'action')),
  action_request_id  text,  -- FK to app.action_requests added in Phase 3
  reason             text,
  created_at         timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (order_id, currency) REFERENCES app.orders (id, currency),
  CHECK ((source = 'historical') = (action_request_id IS NULL))
);
CREATE INDEX refunds_order_id_idx ON app.refunds (order_id);
ALTER TABLE app.refunds ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TYPE app.refunds FROM PUBLIC;

-- Invariant 9, enforced in the database (the last line; Python checks are the first):
-- succeeded refunds per order never exceed captured payments for that order.
-- The order row is locked so concurrent refunds on one order are checked one at a time.
CREATE FUNCTION app.enforce_refund_within_payments() RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
  captured  bigint;
  refunded  bigint;
BEGIN
  IF NEW.status <> 'succeeded' THEN
    RETURN NEW;
  END IF;
  PERFORM 1 FROM app.orders WHERE id = NEW.order_id FOR UPDATE;
  SELECT coalesce(sum(amount_cents), 0) INTO captured FROM app.payments WHERE order_id = NEW.order_id;
  SELECT coalesce(sum(amount_cents), 0) INTO refunded
    FROM app.refunds
   WHERE order_id = NEW.order_id AND status = 'succeeded' AND id <> NEW.id;
  IF refunded + NEW.amount_cents > captured THEN
    RAISE EXCEPTION 'refund % would exceed captured payments for order %', NEW.id, NEW.order_id
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION app.enforce_refund_within_payments() FROM PUBLIC;

CREATE TRIGGER refunds_within_payments
  BEFORE INSERT OR UPDATE ON app.refunds
  FOR EACH ROW EXECUTE FUNCTION app.enforce_refund_within_payments();

-- Payments are captured facts: never updated or deleted, so a refund check can't be undone later.
CREATE FUNCTION app.reject_payment_change() RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
  RAISE EXCEPTION 'app.payments is append-only' USING ERRCODE = 'restrict_violation';
END;
$$;
REVOKE ALL ON FUNCTION app.reject_payment_change() FROM PUBLIC;

CREATE TRIGGER payments_append_only
  BEFORE UPDATE OR DELETE ON app.payments
  FOR EACH ROW EXECUTE FUNCTION app.reject_payment_change();
