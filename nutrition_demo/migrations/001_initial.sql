CREATE DOMAIN nonnegative AS NUMERIC CHECK (VALUE >= 0 AND VALUE < 'Infinity'::numeric);
CREATE TABLE state_meta (id INT PRIMARY KEY CHECK(id=1), version BIGINT NOT NULL DEFAULT 0);
INSERT INTO state_meta(id) VALUES (1);
CREATE TABLE profile (id INT PRIMARY KEY CHECK(id=1), data JSONB NOT NULL);
CREATE TABLE inventory (
 ingredient_id TEXT PRIMARY KEY, quantity nonnegative NOT NULL, unit TEXT NOT NULL,
 state TEXT NOT NULL, data JSONB NOT NULL DEFAULT '{}'
);
CREATE TABLE cooking_runs (
 id TEXT PRIMARY KEY, recipe_id TEXT NOT NULL, prepared_on DATE NOT NULL,
 request_id TEXT UNIQUE NOT NULL, data JSONB NOT NULL
);
CREATE TABLE cooking_ingredients (
 id TEXT PRIMARY KEY, cooking_run_id TEXT NOT NULL REFERENCES cooking_runs(id),
 ingredient_id TEXT NOT NULL REFERENCES inventory(ingredient_id), quantity nonnegative NOT NULL,
 unit TEXT NOT NULL, data JSONB NOT NULL,
 UNIQUE(cooking_run_id, ingredient_id)
);
CREATE TABLE batches (
 id TEXT PRIMARY KEY, cooking_run_id TEXT NOT NULL REFERENCES cooking_runs(id), name TEXT NOT NULL,
 total_boxes INT NOT NULL CHECK(total_boxes>0),
 remaining_boxes INT NOT NULL CHECK(remaining_boxes>=0 AND remaining_boxes<=total_boxes), data JSONB NOT NULL
);
CREATE TABLE batch_ingredients (
 batch_id TEXT NOT NULL REFERENCES batches(id), cooking_ingredient_id TEXT NOT NULL REFERENCES cooking_ingredients(id),
 quantity nonnegative NOT NULL, unit TEXT NOT NULL, PRIMARY KEY(batch_id,cooking_ingredient_id)
);
CREATE TABLE batch_addons (
 batch_id TEXT NOT NULL REFERENCES batches(id), version INT NOT NULL CHECK(version>0),
 data JSONB NOT NULL, PRIMARY KEY(batch_id,version)
);
CREATE TABLE events (
 id TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES batches(id), eaten_on DATE NOT NULL,
 meal TEXT, boxes INT NOT NULL DEFAULT 1 CHECK(boxes=1), data JSONB NOT NULL
);
CREATE INDEX events_day_idx ON events(eaten_on);
CREATE TABLE inventory_movements (
 id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 ingredient_id TEXT NOT NULL REFERENCES inventory(ingredient_id),
 delta NUMERIC NOT NULL CHECK(delta > '-Infinity'::numeric AND delta < 'Infinity'::numeric),
 cooking_run_id TEXT REFERENCES cooking_runs(id), event_id TEXT REFERENCES events(id),
 kind TEXT NOT NULL, data JSONB NOT NULL DEFAULT '{}'
);
CREATE TABLE previews (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, state_version BIGINT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','confirmed','rejected')),
 data JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 confirmed_at TIMESTAMPTZ
);
CREATE TABLE operations (
 request_id TEXT PRIMARY KEY, input_hash TEXT NOT NULL, result JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE workflow_sessions (
 id TEXT PRIMARY KEY, data JSONB NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE agent_runs (
 id TEXT PRIMARY KEY, settings JSONB NOT NULL, trace JSONB NOT NULL DEFAULT '[]',
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
