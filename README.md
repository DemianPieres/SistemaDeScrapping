# LeadScraper Argentina

Aplicación interna para encontrar **clientes potenciales** a quienes ofrecer
servicios de desarrollo web. Pegás una URL de Google Maps de la zona objetivo,
elegís qué tipo de negocios buscar, y la app:

1. Scrapea negocios reales en una zona radial (1/2/5/10 km).
2. Analiza la presencia digital de cada uno (sitio web, SEO, responsividad,
   redes sociales, tecnologías).
3. Calcula una **puntuación de oportunidad (0-100)** para priorizarlos.
4. Te muestra todo en un dashboard con mapa, filtros, gestión de leads y
   exportación a CSV.

> **Sin login.** La app es para uso interno del equipo: al arrancar entrás
> directo, sin usuarios ni contraseñas.

---

## Cómo arrancarla (paso a paso)

### Requisitos del sistema

Vos ya los tenés todos en este equipo (los verifiqué):

- **Python 3.10+** (`python3 --version` → 3.12.3 ✔)
- **Node.js 18+** (`node --version` → v22 ✔)
- **Chromium o Chrome** + `chromedriver` (`/usr/bin/chromium-browser` y
  `/usr/bin/chromedriver` ✔)

Si en otra máquina faltara Chromium:
```bash
sudo apt install -y chromium-browser chromium-chromedriver
```

### Primer arranque

**Una sola vez** (instalación):

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# (el archivo .env ya está creado y configurado para tu equipo)

# Frontend (en otra terminal)
cd frontend
npm install
```

### Encender la app cada día

Abrís dos terminales, una para cada parte:

**Terminal 1 — Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```
→ API en http://localhost:8000  · Docs en http://localhost:8000/docs

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```
→ Abrí http://localhost:5173

Listo. **No hay login.** Entrás directo al dashboard.

---

## Cómo usar la app

1. Andá a **Nuevo scraping**.
2. Abrí Google Maps en el navegador, **centrá la zona objetivo** (zoom in/out
   hasta tener encuadrada la zona que querés cubrir) y **copiá la URL del
   navegador**. Ejemplo válido:
   `https://www.google.com/maps/@-32.8908,-68.8272,15z`
3. Pegala en el formulario, elegí:
   - **Palabra clave**: `restaurantes`, `gimnasios`, `peluquerías`,
     `dentistas`, `inmobiliarias`, etc.
   - **Radio**: 1, 2, 5 o 10 km.
   - **Máximo de resultados**: empezá con **10-20** para una prueba (~1-2 min).
   - **Analizar sitios web**: ✔ recomendado para tener score completo.
4. Click en **Iniciar scraping**.
5. Mirá la barra de progreso. **Los negocios aparecen en `Resultados` a medida
   que se scrapean** (no esperás a que termine el job entero).
6. En `Resultados`:
   - Filtrá por categoría, ciudad, score mínimo, rating, sin sitio web, etc.
   - Vista lista o **mapa interactivo** (los puntos rojos = más oportunidad).
   - Exportá a CSV con un click.
   - Click en cada negocio → vista detallada con análisis web y sugerencias
     de venta.
7. Marcá los más prometedores como **prospectos** (botón "Guardar").
8. En `Mis prospectos` los gestionás: cambiar estado (nuevo → contactado →
   interesado → cerrado), agregar notas, registrar llamadas/emails/visitas.

### Tiempos esperables

Google Maps tiene su tiempo: cada negocio requiere abrir su ficha y leer todos
los datos. Aproximadamente:

| Resultados | Tiempo aproximado |
| ---------- | ----------------- |
| 10         | 1-2 min           |
| 30         | 3-5 min           |
| 60         | 8-12 min          |

Mientras corre, **podés seguir usando la app**. Los datos aparecen sí o sí en
`Resultados` aunque el job esté en estado "running".

---

## Cosas que tenés que saber del backend

### Base de datos

**No tenés que hacer nada.** La app usa **SQLite** por defecto (un solo archivo
en `backend/leadscraper.db`). Se crea automáticamente al primer arranque junto
con todas las tablas y el "usuario equipo" que firma todas las operaciones.

Si querés borrar todo y empezar de cero:
```bash
rm backend/leadscraper.db
```

Si más adelante querés migrar a PostgreSQL para que varios usuarios del equipo
trabajen contra la misma base, editá `backend/.env`:
```
DATABASE_URL=postgresql+psycopg2://usuario:pass@host:5432/leadscraper
```

### Configuración (`backend/.env`)

Ya está armado y funcionando. Lo más útil para vos:

| Variable                       | Para qué sirve                                   |
| ------------------------------ | ------------------------------------------------ |
| `CHROME_BINARY_PATH`           | `/usr/bin/chromium-browser` (configurado)        |
| `CHROMEDRIVER_PATH`            | `/usr/bin/chromedriver` (configurado)            |
| `SCRAPER_HEADLESS=true`        | Ponelo `false` si querés VER el Chrome scrapeando (debug) |
| `SCRAPER_REQUEST_DELAY_SECONDS=0.4` | Subilo si Google te empieza a pedir CAPTCHA |
| `SCRAPER_MAX_RESULTS_PER_QUERY=40` | Tope superior por job                       |

---

## Troubleshooting frecuente

| Síntoma                                      | Solución                                   |
| -------------------------------------------- | ------------------------------------------ |
| Job queda `failed` con "no chrome binary"    | Verificar `CHROME_BINARY_PATH` en `.env`   |
| El scraping no encuentra nada                | URL de Google Maps **sin coordenadas**. Hacé un zoom o moveté el mapa para que la URL incluya `@lat,lng,zoomz` |
| Demasiado lento                              | Bajá `max_results`, o ampliá radio para repartir mejor |
| Google Maps muestra CAPTCHA                  | Subir delay a 1.5+, esperar 30 min, o bajar volumen |
| Frontend muestra "Network error"             | El backend no está corriendo en :8000      |
| Quiero ver al Chrome scrapeando en vivo      | `SCRAPER_HEADLESS=false` en `.env` y reiniciar backend |

---

## Arquitectura (referencia rápida)

```
backend/         FastAPI + Selenium scraper + análisis web
├── app/
│   ├── api/         rutas REST (auth, scraping, businesses, leads, stats)
│   ├── models/      SQLAlchemy ORM (User, Business, ScrapingJob, Lead)
│   ├── services/    maps_scraper, website_analyzer, lead_generator, job_runner
│   └── utils/       database, helpers (geo, normalización)
└── tests/

frontend/        SPA React 18 + Vite + Tailwind + Leaflet + Recharts
└── src/
    ├── components/  Layout, Map, BusinessCard, Filters, StatCard
    ├── pages/       Dashboard, Scrape, Results, BusinessDetail, Leads
    └── services/    cliente axios

docker-compose.yml  (opcional: backend + frontend + Postgres en containers)
```

### Stack

| Capa            | Tecnología                                                  |
| --------------- | ----------------------------------------------------------- |
| Backend         | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic 2           |
| Scraping        | Selenium + Chromium headless, BeautifulSoup, Requests       |
| BD por defecto  | SQLite (sin instalación) — opción PostgreSQL via env        |
| Tareas async    | `BackgroundTasks` de FastAPI                                |
| Frontend        | React 18, Vite, Tailwind CSS, React Router, Axios           |
| Mapas / charts  | Leaflet + react-leaflet · Recharts                          |
| Despliegue      | Docker / docker-compose (opcional)                          |

---

## Modelo de puntuación de oportunidad

`backend/app/services/lead_generator.py`. Cada negocio recibe un score 0-100:

| Señal                                            | Puntos aprox. |
| ------------------------------------------------ | ------------- |
| **No tiene sitio web**                           | **+70**       |
| Sitio web no responde / está caído               | +55           |
| No es responsivo (mobile)                        | +25           |
| Sin meta description / título / HTTPS / favicon  | +2 a +8       |
| Carga lenta (>4s)                                | +8            |
| Stack desactualizado (jQuery solo, WP viejo)     | +6 a +9       |
| Buena reputación (rating ≥ 4.5, 200+ reseñas)    | +12 +8        |
| Sin redes sociales detectadas                    | +4            |

Score acotado a 0-100 con razones explicativas en `opportunity_reasons`.

---

## Endpoints principales

Todos accesibles **sin token**. Documentación interactiva en `/docs`.

| Método | Endpoint                         | Descripción                        |
| ------ | -------------------------------- | ---------------------------------- |
| GET    | `/api/auth/me`                   | Usuario default (informativo)      |
| POST   | `/api/scraping/jobs`             | Lanzar un nuevo job                |
| GET    | `/api/scraping/jobs`             | Listar jobs                        |
| GET    | `/api/scraping/jobs/{id}`        | Estado / progreso                  |
| POST   | `/api/scraping/jobs/{id}/cancel` | Cancelar                           |
| GET    | `/api/businesses`                | Listado paginado y filtrado        |
| GET    | `/api/businesses/map`            | Geo-puntos para el mapa            |
| GET    | `/api/businesses/{id}`           | Detalle completo                   |
| GET    | `/api/businesses/export/csv`     | Exportar a CSV                     |
| GET    | `/api/leads`                     | Mis prospectos                     |
| POST   | `/api/leads`                     | Guardar negocio como prospecto     |
| PUT    | `/api/leads/{id}`                | Cambiar estado / notas / prioridad |
| DELETE | `/api/leads/{id}`                | Eliminar                           |
| POST   | `/api/leads/{id}/interactions`   | Registrar contacto                 |
| GET    | `/api/stats`                     | Estadísticas para el dashboard     |

---

## Tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

16 tests cubriendo helpers geográficos, scoring de oportunidad y endpoints.

---

## Limitaciones

- **Anti-bot Google Maps:** si scrapeás de forma intensiva (>50 jobs/día) puede
  empezar a pedir CAPTCHA. Subí `SCRAPER_REQUEST_DELAY_SECONDS` a 2.0+ y dale
  espacios entre jobs.
- **Selectores DOM:** Google cambia su frontend periódicamente. Los extractores
  usan rutas defensivas con varias alternativas, pero si un día algo deja de
  extraerse (ej: ya no aparece el teléfono), revisá `services/maps_scraper.py`.
- **Sitios web complejos:** el analizador es heurístico (sin claves de pago).
  Detecta lo común (WordPress, Shopify, React, Vue, Bootstrap, jQuery). No
  sustituye un Lighthouse profesional.

---

¿Algo no funciona como esperabas? Mirá los logs del backend en la terminal
donde corre `uvicorn` — siempre dicen claramente en qué punto falló.
