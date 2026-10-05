CREATE TABLE IF NOT EXISTS traderlab_runs (
  id text PRIMARY KEY,
  bot_id text NOT NULL,
  source text NOT NULL CHECK (source IN ('native', 'paper')),
  label text NOT NULL,
  symbol text NOT NULL,
  last_seq bigint NOT NULL DEFAULT 0,
  last_ingest_at timestamptz NOT NULL DEFAULT now(),
  last_event_received_at timestamptz
);
CREATE TABLE IF NOT EXISTS traderlab_events (
  run_id text NOT NULL REFERENCES traderlab_runs(id),
  seq bigint NOT NULL CHECK(seq > 0),
  event_time timestamptz,
  received_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL,
  PRIMARY KEY(run_id, seq)
);
CREATE TABLE IF NOT EXISTS traderlab_login_limits (
  id text PRIMARY KEY, attempts integer NOT NULL, expires_at timestamptz NOT NULL
);

-- One transaction per batch; a conflicting retry aborts the entire batch.
-- The server never overwrites an existing event or changes a run's identity.
CREATE OR REPLACE FUNCTION traderlab_ingest(run jsonb, rows jsonb)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE prior traderlab_runs%ROWTYPE; item jsonb; expected bigint; inserted integer := 0; existing jsonb;
BEGIN
  INSERT INTO traderlab_runs(id, bot_id, source, label, symbol)
    VALUES(run->>'id', run->>'bot_id', run->>'source', run->>'label', run->>'symbol')
    ON CONFLICT(id) DO NOTHING;
  SELECT * INTO prior FROM traderlab_runs WHERE id = run->>'id' FOR UPDATE;
  IF prior.bot_id <> run->>'bot_id' OR prior.source <> run->>'source' OR prior.symbol <> run->>'symbol' OR prior.label <> run->>'label' THEN
    RAISE EXCEPTION 'RUN_IDENTITY_CONFLICT';
  END IF;
  expected := prior.last_seq;
  FOR item IN SELECT value FROM jsonb_array_elements(rows) LOOP
    IF (item->>'seq')::bigint <= expected THEN
      SELECT payload INTO existing FROM traderlab_events WHERE run_id = prior.id AND seq = (item->>'seq')::bigint;
      IF existing IS NULL OR existing <> item THEN RAISE EXCEPTION 'EVENT_IDENTITY_CONFLICT'; END IF;
    ELSE
      IF (item->>'seq')::bigint <> expected + 1 THEN RAISE EXCEPTION 'SEQUENCE_GAP'; END IF;
      INSERT INTO traderlab_events(run_id, seq, event_time, payload)
        VALUES(prior.id, (item->>'seq')::bigint, (item->>'time')::timestamptz, item);
      expected := (item->>'seq')::bigint;
      inserted := inserted + 1;
    END IF;
  END LOOP;
  UPDATE traderlab_runs SET last_seq = expected, last_ingest_at = now(),
    last_event_received_at = CASE WHEN inserted > 0 THEN now() ELSE last_event_received_at END WHERE id = prior.id;
  RETURN jsonb_build_object('accepted', inserted, 'last_seq', expected);
END;
$$;
