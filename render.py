#!/usr/bin/env python3
"""27th News — render de una edición: JSON curado → portada del día + un artículo
por noticia + índice histórico, con el estilo Orbit.

POR QUÉ PYTHON PURO (stdlib): corre en la VM efímera de la routine de Claude Code.
Cero dependencias = nada que instalar. El diseño lo controlan orbit-style.css (la
hoja de Lugardo) y periodico.css; aquí solo se arma la estructura.

Estructura que produce:
    ediciones/AAAA-MM-DD.html          portada del día (lista de noticias)
    ediciones/AAAA-MM-DD/slug.html     un artículo completo por noticia
    ediciones/index.html               archivo histórico (todas las ediciones)
    ediciones/metadata.json            titular por fecha (para el índice)

Uso:  python3 render.py edicion.json      (o  -  para leer de stdin)
"""
import html
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone, timedelta

NOMBRE = "27th News"
LEMA = "Las noticias de inteligencia artificial, cada mañana."
TZ = timezone(timedelta(hours=-7))         # America/Mazatlan (Culiacán, sin DST)
AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_EDICIONES = os.path.join(AQUI, "ediciones")

CATEGORIAS = {
    "modelos": "Modelos", "agentic-coding": "Agentic coding", "tooling": "Herramientas",
    "infra": "Infraestructura", "investigacion": "Investigación",
    "producto": "Producto", "otro": "General",
}
MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Tema claro/oscuro: sigue al dispositivo por defecto y recuerda la elección.
SCRIPT_TEMA = """<script>
(function(){try{var t=localStorage.getItem('27th-tema');
if(!t)t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
if(t==='dark')document.documentElement.classList.add('dark');}catch(e){}})();
function toggleTema(){var d=document.documentElement.classList.toggle('dark');
try{localStorage.setItem('27th-tema',d?'dark':'light');}catch(e){}}
</script>"""

# Botón de tema con ICONO SVG plano (line). El CSS muestra luna en claro / sol en oscuro.
BOTON_TEMA = """<button class="np-tema" onclick="toggleTema()" aria-label="Cambiar tema">
<svg class="ico ico-luna" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
<svg class="ico ico-sol" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
</button>"""


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def fecha_larga(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} de {MESES[d.month]} de {d.year}"


def _cat(clave: str) -> str:
    return CATEGORIAS.get(clave, "General")


def _dominio(url: str) -> str:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url or "")
    return m.group(1) if m else "fuente"


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:60] or "nota"


def _head(titulo: str) -> str:
    return f"""<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(titulo)}</title>
<link rel="stylesheet" href="/orbit-style.css">
<link rel="stylesheet" href="/periodico.css">
{SCRIPT_TEMA}
</head>"""


def _cuerpo_html(cuerpo: str) -> str:
    """Cuerpo del artículo → párrafos. Una línea que empieza con '## ' se vuelve
    subtítulo de sección; las líneas en blanco separan párrafos."""
    partes, buf = [], []

    def cerrar():
        if buf:
            partes.append(f"<p>{esc(' '.join(buf))}</p>")
            buf.clear()

    for linea in (cuerpo or "").splitlines():
        s = linea.strip()
        if not s:
            cerrar()
        elif s.startswith("## "):
            cerrar()
            partes.append(f'<h2 class="np-art__sub">{esc(s[3:].strip())}</h2>')
        else:
            buf.append(s)
    cerrar()
    return "".join(partes)


def _fuentes_html(fuentes: list) -> str:
    items = "".join(
        f'<li><a class="link-muted" href="{esc(f.get("url"))}" target="_blank" '
        f'rel="noopener">{esc(f.get("nombre") or _dominio(f.get("url")))} ↗</a></li>'
        for f in (fuentes or []) if f.get("url"))
    if not items:
        return ""
    return f'<div class="np-fuentes"><div class="np-fuentes__tit">Fuentes</div><ul>{items}</ul></div>'


# ── portada del día: una card por noticia, clickeable ────────────────────────
def card_noticia(fecha: str, a: dict) -> str:
    slug = a.get("slug") or slugify(a.get("titulo", ""))
    return f"""
        <a class="np-card" href="/{fecha}/{esc(slug)}">
          <span class="np-card__cat">{esc(_cat(a.get("categoria")))}</span>
          <h3 class="np-card__title">{esc(a.get("titulo"))}</h3>
          <p class="np-card__resumen">{esc(a.get("resumen"))}</p>
          <span class="np-card__mas">Leer nota →</span>
        </a>"""


def render_portada(data: dict) -> str:
    fecha = data["fecha"]
    cards = "\n".join(card_noticia(fecha, a) for a in data.get("articulos", []))
    editorial = f'<p class="np-editorial">{esc(data["editorial"])}</p>' if data.get("editorial") else ""
    return f"""<!doctype html>
<html lang="es">
{_head(f"{NOMBRE} · {fecha_larga(fecha)}")}
<body>
  {BOTON_TEMA}
  <div class="container np-wrap">
    <header class="np-masthead">
      <div class="np-kicker-top">Edición diaria</div>
      <a href="/" class="np-logo">{esc(NOMBRE)}</a>
      <div class="np-fecha">{esc(fecha_larga(fecha))}</div>
      <div class="np-titular">{esc(data.get("titular_del_dia"))}</div>
      {editorial}
    </header>
    <main class="np-grid">
      {cards}
    </main>
    <footer class="np-footer">
      <a class="np-btn" href="/"><span>←</span> Todas las ediciones</a>
      <span>{esc(NOMBRE)} — {esc(LEMA)}</span>
    </footer>
  </div>
</body>
</html>"""


# ── artículo individual ──────────────────────────────────────────────────────
def render_articulo(fecha: str, a: dict) -> str:
    cuerpo = _cuerpo_html(a.get("cuerpo") or a.get("resumen") or "")
    dek = f'<p class="np-art__dek">{esc(a["resumen"])}</p>' if a.get("resumen") else ""
    return f"""<!doctype html>
<html lang="es">
{_head(f"{esc(a.get('titulo'))} · {NOMBRE}")}
<body>
  {BOTON_TEMA}
  <div class="container-narrow np-wrap">
    <a class="np-volver" href="/{fecha}">← {esc(fecha_larga(fecha))}</a>
    <article class="np-articulo">
      <span class="np-card__cat">{esc(_cat(a.get("categoria")))}</span>
      <h1 class="np-art__title">{esc(a.get("titulo"))}</h1>
      {dek}
      <div class="np-art__cuerpo">{cuerpo}</div>
      {_fuentes_html(a.get("fuentes"))}
    </article>
    <footer class="np-footer">
      <a class="np-btn" href="/{fecha}"><span>←</span> Volver a la edición</a>
    </footer>
  </div>
</body>
</html>"""


# ── índice histórico ─────────────────────────────────────────────────────────
def _ediciones_existentes() -> list:
    if not os.path.isdir(DIR_EDICIONES):
        return []
    return sorted((f[:-5] for f in os.listdir(DIR_EDICIONES)
                   if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.html", f)), reverse=True)


def render_indice(titulares: dict) -> str:
    fechas = _ediciones_existentes()
    tarjetas = "\n".join(f"""
        <a class="np-card" href="/{f}">
          <span class="np-card__cat">{esc(fecha_larga(f))}</span>
          <h3 class="np-card__title">{esc(titulares.get(f, "Edición del día"))}</h3>
          <span class="np-card__mas">Abrir edición →</span>
        </a>""" for f in fechas)
    cuerpo = f'<main class="np-grid">{tarjetas}</main>' if fechas else \
        '<p class="np-editorial">Aún no hay ediciones. La primera llega mañana a las 6 AM.</p>'
    return f"""<!doctype html>
<html lang="es">
{_head(f"{NOMBRE} · Ediciones")}
<body>
  {BOTON_TEMA}
  <div class="container np-wrap">
    <header class="np-masthead">
      <div class="np-kicker-top">Archivo</div>
      <div class="np-logo">{esc(NOMBRE)}</div>
      <div class="np-fecha">{esc(LEMA)}</div>
    </header>
    {cuerpo}
  </div>
</body>
</html>"""


def _titulares() -> dict:
    try:
        return json.load(open(os.path.join(DIR_EDICIONES, "metadata.json")))
    except Exception:
        return {}


def main():
    if len(sys.argv) < 2:
        sys.exit("uso: render.py <edicion.json | ->")
    crudo = sys.stdin.read() if sys.argv[1] == "-" else open(sys.argv[1], encoding="utf-8").read()
    crudo = crudo.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(crudo)

    fecha = data["fecha"]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        sys.exit(f"fecha inválida: {fecha}")
    if not data.get("articulos"):
        sys.exit("la edición no trae artículos; no se escribe nada")

    # asegurar slug único por artículo
    vistos = set()
    for a in data["articulos"]:
        s = a.get("slug") or slugify(a.get("titulo", ""))
        while s in vistos:
            s += "-2"
        a["slug"] = s
        vistos.add(s)

    os.makedirs(DIR_EDICIONES, exist_ok=True)
    # 1) portada del día
    with open(os.path.join(DIR_EDICIONES, f"{fecha}.html"), "w", encoding="utf-8") as f:
        f.write(render_portada(data))
    # 2) un artículo por noticia (en subcarpeta de la fecha)
    dir_dia = os.path.join(DIR_EDICIONES, fecha)
    os.makedirs(dir_dia, exist_ok=True)
    for a in data["articulos"]:
        with open(os.path.join(dir_dia, f"{a['slug']}.html"), "w", encoding="utf-8") as f:
            f.write(render_articulo(fecha, a))
    # 3) metadata + índice
    meta = _titulares()
    meta[fecha] = data.get("titular_del_dia", "")
    with open(os.path.join(DIR_EDICIONES, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    with open(os.path.join(DIR_EDICIONES, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_indice(meta))

    print(f"OK edición {fecha}: {len(data['articulos'])} artículos + portada + índice")


if __name__ == "__main__":
    main()
