# Scripts de utilidad para la aplicación de finanzas

Este directorio contiene scripts útiles para desarrollo y mantenimiento.

## Scripts disponibles

### `clean_transactions.py`
Limpia la tabla de transacciones para pruebas.

**Uso básico:**
```bash
# Desde el directorio raíz del proyecto
python -m app.scripts.clean_transactions

# Modo forzado (sin confirmación)
python -m app.scripts.clean_transactions --force

# Modo avanzado con filtros
python -m app.scripts.clean_transactions --advanced
```

**Opciones del modo avanzado:**
- Eliminar por usuario específico
- Eliminar por fecha
- Eliminar por tipo de transacción
- Eliminar todas

### `reset_last_checked.py`
Resetea la fecha `last_checked` de las cuentas al 1 de agosto de 2025 00:00 UTC.

**Uso básico:**
```bash
# Resetear todas las cuentas al 1 de agosto 2025
python -m app.scripts.reset_last_checked

# Modo forzado (sin confirmación)
python -m app.scripts.reset_last_checked --force

# Listar estado actual de cuentas
python -m app.scripts.reset_last_checked --list
```

**Opciones avanzadas:**
```bash
# Fecha personalizada
python -m app.scripts.reset_last_checked --date "2025-07-15"
python -m app.scripts.reset_last_checked --date "2025-07-15 12:30:00"

# Cuentas específicas
python -m app.scripts.reset_last_checked --accounts "1,2,3"

# Combinaciones
python -m app.scripts.reset_last_checked --accounts "1" --date "2025-07-01" --force
```

### `create_initial_user.py`
Crea usuario y cuenta inicial (ya existente).

**Uso:**
```bash
python -m app.scripts.create_initial_user
```

## Ejemplos para pruebas

```bash
# Limpiar datos y resetear fechas para nueva prueba
python -m app.scripts.clean_transactions -f
python -m app.scripts.reset_last_checked -f

# Ver estado actual
python -m app.scripts.reset_last_checked --list

# Reset específico con fecha personalizada
python -m app.scripts.reset_last_checked --accounts "1" --date "2025-08-13 18:00:00"
```
