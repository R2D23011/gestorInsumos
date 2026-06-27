# Migraciones de base de datos (Alembic)

El esquema de la base lo gestiona **Alembic**. Ya **no** se usa `create_all`
al arrancar la app (se eliminó de `app/main.py`).

## Comandos del día a día

```bash
# Activar el venv primero (Windows / Git Bash)
source venv/Scripts/activate

# Aplicar las migraciones pendientes (crea/actualiza tablas)
alembic upgrade head

# Ver en qué revisión está la base
alembic current

# Tras cambiar un modelo en app/models.py, generar una nueva migración
alembic revision --autogenerate -m "descripcion del cambio"
# Revisar el archivo generado en alembic/versions/ y luego:
alembic upgrade head
```

La URL de conexión se toma de `DATABASE_URL` (archivo `.env`) automáticamente
desde `alembic/env.py`; no hace falta ponerla en `alembic.ini`.

## Primera vez contra Supabase (base que ya tiene datos/tablas)

1. Corre el script `supabase_migration.sql` en el SQL Editor de Supabase
   (elige Caso A o Caso B según lo que ya exista).
2. Marca la migración inicial como aplicada **sin** re-ejecutarla:
   ```bash
   alembic stamp head
   ```
   Esto solo escribe la versión en la tabla `alembic_version`.

> Nota Supabase: para correr migraciones usa la conexión **directa**
> (puerto 5432) o el *Session Pooler*, no el *Transaction Pooler* (6543),
> que no soporta sentencias DDL/transaccionales largas.

## Despliegue (Render)

Como ya no se crean las tablas solas, el comando de arranque debe correr las
migraciones antes de levantar la API. En Render, *Start Command*:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
