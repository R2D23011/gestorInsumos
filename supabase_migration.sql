-- ============================================================
--  Migración manual para Supabase (Postgres)
--  Objetivo: dejar el esquema igual al modelo actual
--  (Hospital con columna `state` y `city` opcional + Need)
-- ============================================================

-- ------------------------------------------------------------
-- PASO 0 — Inspeccionar qué existe HOY en tu base
-- Ejecuta esto primero en el SQL Editor de Supabase y mira el
-- resultado para saber qué caso aplica.
-- ------------------------------------------------------------
SELECT table_name, column_name, is_nullable, data_type
FROM information_schema.columns
WHERE table_name IN ('hospitals', 'needs', 'inventory', 'needs_history')
ORDER BY table_name, ordinal_position;


-- ============================================================
-- CASO A — Ya tienes las tablas `hospitals` y `needs`
--          (de la versión anterior, sin la columna `state`).
--          Esto es lo más probable. Ejecuta estos ALTER:
-- ============================================================

-- 1) Agregar `state` (primero como NULL para no romper filas existentes)
ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS state VARCHAR;

-- 2) Rellenar filas viejas que quedaron sin estado
--    (ajusta el valor si sabes a qué estado pertenecen)
UPDATE hospitals SET state = 'Distrito Capital' WHERE state IS NULL;

-- 3) Hacer `state` obligatoria, como en el modelo
ALTER TABLE hospitals ALTER COLUMN state SET NOT NULL;

-- 4) Índice para el filtro por estado
CREATE INDEX IF NOT EXISTS ix_hospitals_state ON hospitals (state);

-- 5) `city` pasa a ser opcional
ALTER TABLE hospitals ALTER COLUMN city DROP NOT NULL;


-- ============================================================
-- CASO B — La base está vacía o solo tiene las tablas viejas
--          `inventory` / `needs_history`. Crea el esquema
--          completo desde cero:
-- ============================================================

-- (Opcional) Eliminar las tablas viejas que ya no se usan:
-- DROP TABLE IF EXISTS needs_history;
-- DROP TABLE IF EXISTS inventory;

CREATE TABLE IF NOT EXISTS hospitals (
    id SERIAL NOT NULL,
    name VARCHAR NOT NULL,
    state VARCHAR NOT NULL,
    city VARCHAR,
    address VARCHAR,
    phone VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS ix_hospitals_city  ON hospitals (city);
CREATE INDEX IF NOT EXISTS ix_hospitals_id    ON hospitals (id);
CREATE INDEX IF NOT EXISTS ix_hospitals_state ON hospitals (state);

CREATE TABLE IF NOT EXISTS needs (
    id SERIAL NOT NULL,
    hospital_id INTEGER NOT NULL,
    supply_name VARCHAR NOT NULL,
    quantity_needed INTEGER NOT NULL,
    urgency VARCHAR NOT NULL,
    contact_name VARCHAR,
    contact_phone VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (hospital_id) REFERENCES hospitals (id)
);
CREATE INDEX IF NOT EXISTS ix_needs_id ON needs (id);


-- ============================================================
-- IMPORTANTE — Después de correr el CASO A o el CASO B:
-- Tu base ya coincide con la migración inicial de Alembic.
-- Para que Alembic lo sepa (y NO intente recrear las tablas),
-- marca la migración como aplicada SIN ejecutarla, desde tu
-- terminal local apuntando a la DATABASE_URL de Supabase:
--
--     alembic stamp head
--
-- A partir de ahí, cualquier cambio de esquema futuro es:
--     alembic revision --autogenerate -m "descripcion"
--     alembic upgrade head
-- ============================================================
