# 27th News — periódico diario de noticias de IA

Cada día a las **6:00 AM (Culiacán)** una **routine de Claude Code** busca las
noticias de IA de las últimas 24 h, redacta un artículo por noticia y publica la
edición. Corre con la **suscripción** (no API, sin costo por token). El VPS jala
este repo y sirve las ediciones bajo `noticias.27th.cloud`.

```
routine (nube, 6 AM) → web search → edicion.json → python3 render.py → git push
        │
        ▼
   VPS → git pull → sirve la edición del día + una página por noticia   (consultable 7 AM)
```

## Estructura del sitio que se genera

- `ediciones/AAAA-MM-DD.html` — **portada del día**: lista de noticias (cada cuadro lleva la categoría tenue arriba del título y enlaza a su artículo).
- `ediciones/AAAA-MM-DD/slug.html` — **un artículo por noticia**: título, cuerpo completo y las fuentes usadas.
- `ediciones/index.html` — **archivo histórico**: todas las ediciones (se pueden consultar días anteriores).
- `ediciones/metadata.json` — titular de cada fecha (para el índice).

Archivos del repo: `render.py` (Python puro, sin dependencias), `orbit-style.css`
(diseño base), `periodico.css` (capa periódico). URLs limpias: `/AAAA-MM-DD` y
`/AAAA-MM-DD/slug`.

## Schema del `edicion.json`

```json
{
  "fecha": "AAAA-MM-DD",
  "titular_del_dia": "una frase que resume el día",
  "editorial": "opcional, 2-3 frases de contexto",
  "articulos": [
    {
      "titulo": "string",
      "resumen": "1-2 frases para la portada",
      "cuerpo": "el artículo completo: 2-4 párrafos separados por línea en blanco",
      "categoria": "modelos | agentic-coding | tooling | infra | investigacion | producto | otro",
      "relevancia": 1,
      "fuentes": [{ "nombre": "string", "url": "https://..." }]
    }
  ]
}
```

`slug` es opcional: si no lo pones, `render.py` lo genera del título.

---

## PROMPT DE LA ROUTINE (pegar en claude.ai/code/routines)

> Conecta este repo, programa **cada día a las 6:00 AM America/Mazatlan**, y usa este prompt:

```
Eres el editor de "27th News", un periódico diario de noticias de Inteligencia
Artificial para un lector técnico (desarrollador/diseñador). Trabajas en este repo.

Cada corrida:

1. BUSCA en la web las noticias REALES de IA publicadas en las ÚLTIMAS 24 HORAS.
   REVISA SIEMPRE, PRIMERO, estas 3 fuentes oficiales para no perderte lanzamientos
   de modelos (son prioritarias):
     - https://openai.com/es-419/news/
     - https://www.anthropic.com/news
     - https://blog.google/products-and-platforms/products/gemini/
   Luego haz varias búsquedas más para cubrir: modelos nuevos, releases y features,
   agentic coding, herramientas para desarrolladores, infraestructura, papers
   relevantes y productos. Usa la fecha de hoy como referencia.

2. CURA entre 6 y 12 notas:
   - Solo hechos verificables: lanzamientos, releases, features, papers, anuncios
     oficiales. DESCARTA rumores, opinión, especulación, listicles y clickbait.
   - Prioriza impacto para quien desarrolla software.
   - Reúne TODAS las fuentes con URL real que usaste para cada nota (pueden ser
     varias); consérvalas todas, no solo una.

3. ESCRIBE el archivo `edicion.json` en la raíz del repo, JSON válido y NADA más
   (sin markdown, sin ```), con esta estructura EXACTA:
   {
     "fecha": "<HOY en AAAA-MM-DD>",
     "titular_del_dia": "<una frase que resuma el día>",
     "editorial": "<opcional, 2-3 frases de contexto>",
     "articulos": [
       {
         "titulo": "...",
         "resumen": "<1-2 frases para la portada>",
         "cuerpo": "<el artículo completo, 2-4 párrafos separados por una línea en blanco>",
         "categoria": "modelos|agentic-coding|tooling|infra|investigacion|producto|otro",
         "relevancia": 1,
         "fuentes": [{"nombre":"...","url":"https://..."}]
       }
     ]
   }
   Reglas de redacción: TODO EN ESPAÑOL, en TUS PROPIAS PALABRAS. NUNCA copies
   frases textuales de los artículos. El `resumen` es corto (1-2 frases): sirve de
   gancho en el cuadro de la portada Y de bajada (subtítulo) bajo el titular del
   artículo. El `cuerpo` es el artículo en sí: 2-4 párrafos que expliquen qué pasó,
   por qué importa y qué implica para quien desarrolla, separando cada párrafo con
   una línea en blanco. Si una nota es larga y lo amerita, puedes dividir el cuerpo
   con SUBTÍTULOS de sección: una línea que empiece con "## " y el subtítulo (ej.
   "## Por qué importa"); úsalos con moderación, solo cuando ayuden. Conserva nombres
   propios y términos técnicos en inglés. `relevancia` de 1 (menor) a 5 (mayor). NO
   inventes imágenes ni URLs: usa solo enlaces reales de los resultados de búsqueda.

4. GENERA el HTML corriendo:  python3 render.py edicion.json
   (crea la portada del día, una página por artículo y actualiza el índice).

5. Haz git add de los cambios en `ediciones/`, commit con mensaje
   "Edición <fecha>", y haz **push directo a la rama main**:
       git push origin HEAD:main
   (Es importante que sea a `main`: el VPS publica desde esa rama.)

Si la búsqueda no arroja noticias suficientes o el render falla, NO publiques una
edición vacía: describe el problema y termina sin commitear.
```
