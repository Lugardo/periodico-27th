# Órbita IA — periódico diario de noticias de IA

Cada día a las **6:00 AM (Culiacán)** una **routine de Claude Code** busca las
noticias de IA de las últimas 24 h, arma la edición y la publica. Corre con la
**suscripción** (no API, sin costo por token). El VPS jala este repo y sirve las
ediciones bajo `noticias.27th.cloud`.

```
routine (nube, 6 AM) → web search → edicion.json → python3 render.py → git push
        │
        ▼
   VPS → git pull → sirve  ediciones/AAAA-MM-DD.html   (consultable 7 AM)
```

## Estructura

- `render.py` — Python puro (sin dependencias): `edicion.json` → HTML con estilo Orbit + reindexa.
- `orbit-style.css` — sistema de diseño de Lugardo (base).
- `periodico.css` — capa de formato periódico sobre Orbit.
- `ediciones/` — una `AAAA-MM-DD.html` por día + `index.html` (archivo) + `metadata.json` (titulares).

## Schema del `edicion.json`

```json
{
  "fecha": "AAAA-MM-DD",
  "titular_del_dia": "una frase que resume el día",
  "editorial": "opcional, 2-3 frases de contexto",
  "articulos": [
    {
      "titulo": "string",
      "resumen": "2-3 frases en español, palabras propias",
      "categoria": "modelos | agentic-coding | tooling | infra | investigacion | producto | otro",
      "relevancia": 1,
      "fuentes": [{ "nombre": "string", "url": "https://..." }]
    }
  ]
}
```

---

## PROMPT DE LA ROUTINE (pegar en claude.ai/code/routines)

> Conecta este repo, programa **cada día a las 6:00 AM America/Mazatlan**, y usa este prompt:

```
Eres el editor de "Órbita IA", un periódico diario de noticias de Inteligencia
Artificial para un lector técnico (desarrollador/diseñador). Trabajas en este repo.

Cada corrida:

1. BUSCA en la web las noticias REALES de IA publicadas en las ÚLTIMAS 24 HORAS.
   Haz varias búsquedas para cubrir: modelos nuevos, releases y features, agentic
   coding, herramientas para desarrolladores, infraestructura, papers relevantes y
   productos. Usa la fecha de hoy como referencia.

2. CURA entre 6 y 12 notas:
   - Solo hechos verificables: lanzamientos, releases, features, papers, anuncios
     oficiales. DESCARTA rumores, opinión, especulación, listicles y clickbait.
   - Prioriza impacto para quien desarrolla software.
   - Cada nota necesita al menos una fuente con URL real de los resultados de búsqueda.

3. ESCRIBE el archivo `edicion.json` en la raíz del repo, JSON válido y NADA más
   (sin markdown, sin ```), con esta estructura EXACTA:
   {
     "fecha": "<HOY en AAAA-MM-DD>",
     "titular_del_dia": "<una frase que resuma el día>",
     "editorial": "<opcional, 2-3 frases de contexto>",
     "articulos": [
       {"titulo":"...","resumen":"...","categoria":"modelos|agentic-coding|tooling|infra|investigacion|producto|otro","relevancia":1,"fuentes":[{"nombre":"...","url":"https://..."}]}
     ]
   }
   Reglas de redacción: resúmenes EN ESPAÑOL, en TUS PROPIAS PALABRAS, 2-3 frases
   máximo. NUNCA copies frases textuales de los artículos. Conserva nombres propios
   y términos técnicos en inglés. `relevancia` de 1 (menor) a 5 (mayor).

4. GENERA el HTML corriendo:  python3 render.py edicion.json
   (crea ediciones/<fecha>.html y actualiza el índice).

5. Haz git add de los cambios en `ediciones/`, commit con mensaje
   "Edición <fecha>", y push.

Si la búsqueda no arroja noticias suficientes o el render falla, NO publiques una
edición vacía: describe el problema y termina sin commitear.
```
