#!/usr/bin/env python3
"""Periódico IA — render de una edición: JSON curado → HTML con estilo Orbit.

POR QUÉ PYTHON PURO (stdlib): esto corre en la VM efímera de la routine de Claude
Code en la nube. Cero dependencias = nada que instalar, nada que se rompa. El
diseño lo controla `orbit-style.css` (la hoja de Lugardo); aquí solo se arma la
estructura HTML usando SUS clases (.container, .section-title, .feature-card…).

Uso:
    python3 render.py edicion.json        # → ediciones/AAAA-MM-DD.html + reindexa
    python3 render.py -                    # lee el JSON de stdin

El JSON de entrada sigue el schema del prompt de la routine (ver README).
"""
import html
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

NOMBRE = "Órbita IA"                       # nombre del periódico (editable)
LEMA = "Las noticias de inteligencia artificial, cada mañana."
TZ = timezone(timedelta(hours=-7))         # America/Mazatlan (Culiacán, sin DST)
AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_EDICIONES = os.path.join(AQUI, "ediciones")

# Orden y etiqueta legible de las categorías del schema.
CATEGORIAS = [
    ("modelos", "Modelos"),
    ("agentic-coding", "Agentic coding"),
    ("tooling", "Herramientas"),
    ("infra", "Infraestructura"),
    ("investigacion", "Investigación"),
    ("producto", "Producto"),
    ("otro", "Otras"),
]
MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def fecha_larga(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} de {MESES[d.month]} de {d.year}"


def _dominio(url: str) -> str:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url or "")
    return m.group(1) if m else "fuente"


def card_articulo(a: dict) -> str:
    """Una nota como .feature-card del sistema Orbit."""
    fuentes = a.get("fuentes") or []
    links = " · ".join(
        f'<a class="link-muted" href="{esc(f.get("url"))}" target="_blank" '
        f'rel="noopener">{esc(f.get("nombre") or _dominio(f.get("url")))} ↗</a>'
        for f in fuentes if f.get("url"))
    return f"""
        <article class="feature-card np-card">
          <div class="feature-card__header">
            <span class="feature-card__label">{esc(_cat_label(a.get("categoria")))}</span>
          </div>
          <h3 class="feature-card__title np-card__title">{esc(a.get("titulo"))}</h3>
          <p class="np-card__resumen">{esc(a.get("resumen"))}</p>
          <div class="np-card__fuentes">{links}</div>
        </article>"""


def _cat_label(clave: str) -> str:
    for k, etq in CATEGORIAS:
        if k == clave:
            return etq
    return "Otras"


def seccion(clave: str, etiqueta: str, articulos: list) -> str:
    cards = "\n".join(card_articulo(a) for a in articulos)
    return f"""
      <section class="np-seccion">
        <div class="section-kicker np-kicker">{esc(etiqueta)}</div>
        <div class="np-grid">{cards}
        </div>
      </section>"""


def render_edicion(data: dict) -> str:
    fecha = data["fecha"]
    arts = data.get("articulos") or []
    # agrupar por categoría respetando el orden de CATEGORIAS
    por_cat = {}
    for a in arts:
        por_cat.setdefault(a.get("categoria", "otro"), []).append(a)
    secciones = "\n".join(
        seccion(k, etq, por_cat[k]) for k, etq in CATEGORIAS if por_cat.get(k))

    editorial = ""
    if data.get("editorial"):
        editorial = f'<p class="np-editorial">{esc(data["editorial"])}</p>'

    return f"""<!doctype html>
<html lang="es" class="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(NOMBRE)} · {fecha_larga(fecha)}</title>
<link rel="stylesheet" href="/orbit-style.css">
<link rel="stylesheet" href="/periodico.css">
</head>
<body>
  <div class="container np-wrap">
    <header class="np-masthead">
      <div class="eyebrow np-eyebrow">Edición diaria</div>
      <a href="/" class="np-logo">{esc(NOMBRE)}</a>
      <div class="np-fecha">{esc(fecha_larga(fecha))} · Culiacán</div>
      <div class="np-titular">{esc(data.get("titular_del_dia"))}</div>
      {editorial}
    </header>
    <main class="np-main">
      {secciones}
    </main>
    <footer class="np-footer">
      <a class="link-muted" href="/">← Ver todas las ediciones</a>
      <span>{esc(NOMBRE)} — {esc(LEMA)}</span>
    </footer>
  </div>
</body>
</html>"""


def _ediciones_existentes() -> list:
    """Lista de fechas con edición, más nueva primero."""
    if not os.path.isdir(DIR_EDICIONES):
        return []
    fechas = [f[:-5] for f in os.listdir(DIR_EDICIONES)
              if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.html", f)]
    return sorted(fechas, reverse=True)


def render_indice(titulares: dict) -> str:
    """El índice histórico: una tarjeta por edición. `titulares` mapea fecha→titular."""
    fechas = _ediciones_existentes()
    filas = "\n".join(f"""
        <a class="feature-card np-idx" href="/{f}">
          <span class="feature-card__label">{esc(fecha_larga(f))}</span>
          <span class="np-idx__titular">{esc(titulares.get(f, ""))}</span>
        </a>""" for f in fechas)
    hay = bool(fechas)
    cuerpo = f'<div class="np-grid">{filas}</div>' if hay else \
        '<p class="np-editorial">Aún no hay ediciones. La primera llega mañana a las 6 AM.</p>'
    return f"""<!doctype html>
<html lang="es" class="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(NOMBRE)} · Ediciones</title>
<link rel="stylesheet" href="/orbit-style.css">
<link rel="stylesheet" href="/periodico.css">
</head>
<body>
  <div class="container np-wrap">
    <header class="np-masthead">
      <div class="eyebrow np-eyebrow">Archivo</div>
      <div class="np-logo">{esc(NOMBRE)}</div>
      <div class="np-fecha">{esc(LEMA)}</div>
    </header>
    <main class="np-main">
      <section class="np-seccion">
        <div class="section-kicker np-kicker">Todas las ediciones</div>
        {cuerpo}
      </section>
    </main>
  </div>
</body>
</html>"""


def _titulares_conocidos() -> dict:
    """Recupera el titular de cada edición del índice de metadata (metadata.json),
    para no reparsear los HTML. Si no existe, arranca vacío."""
    p = os.path.join(DIR_EDICIONES, "metadata.json")
    try:
        return json.load(open(p))
    except Exception:
        return {}


def main():
    if len(sys.argv) < 2:
        sys.exit("uso: render.py <edicion.json | ->")
    crudo = sys.stdin.read() if sys.argv[1] == "-" else open(sys.argv[1], encoding="utf-8").read()
    # tolerar que el modelo envuelva en ```json
    crudo = crudo.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(crudo)

    fecha = data["fecha"]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        sys.exit(f"fecha inválida: {fecha}")
    if not (data.get("articulos")):
        sys.exit("la edición no trae artículos; no se escribe nada")

    os.makedirs(DIR_EDICIONES, exist_ok=True)
    # 1) la edición del día (sobrescribe si ya existe → idempotente)
    with open(os.path.join(DIR_EDICIONES, f"{fecha}.html"), "w", encoding="utf-8") as f:
        f.write(render_edicion(data))
    # 2) actualizar la metadata (titular por fecha) para el índice
    meta = _titulares_conocidos()
    meta[fecha] = data.get("titular_del_dia", "")
    with open(os.path.join(DIR_EDICIONES, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    # 3) regenerar el índice
    with open(os.path.join(DIR_EDICIONES, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_indice(meta))

    print(f"OK edición {fecha}: {len(data['articulos'])} notas → ediciones/{fecha}.html")


if __name__ == "__main__":
    main()
