# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo", "pandas", "numpy", "scipy", "altair", "folium", "pyarrow"]
# ///
import marimo

__generated_with = "0.18.1"
app = marimo.App(
    width="medium",
    app_title="Standortplanung Schnellladeparks",
    css_file="d3.css",
)


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from pathlib import Path

    # Daten liegen neben dem Notebook in public/ladeinfrastruktur/data
    DATA_DIR = mo.notebook_location() / "public" / "ladeinfrastruktur" / "data"
    return DATA_DIR, mo


@app.cell(hide_code=True)
async def _():
    # Nur in der WebAssembly-Version: Pakete nachladen
    import sys

    if sys.platform == "emscripten":
        import micropip

        for _pkg in ["pandas", "numpy", "scipy", "altair", "folium", "pyarrow"]:
            await micropip.install(_pkg)
    return


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import numpy as np
    import altair as alt
    import folium
    from scipy.spatial import cKDTree
    from scipy.optimize import milp, LinearConstraint, Bounds
    from scipy.sparse import coo_matrix, csr_matrix, hstack as sp_hstack
    import warnings

    warnings.filterwarnings("ignore", message=".*narwhals.*")
    alt.data_transformers.disable_max_rows()
    return (
        Bounds,
        LinearConstraint,
        alt,
        cKDTree,
        coo_matrix,
        csr_matrix,
        folium,
        milp,
        np,
        pd,
        sp_hstack,
    )


@app.cell(hide_code=True)
def _(mo):
    # For WASM compatibility, we inline the slides classes here
    # (marimo doesn't bundle utils/ in WASM exports)
    from __future__ import annotations
    from dataclasses import dataclass
    from typing import Optional as _Optional
    import html as _html

    # Slide constants
    SLIDE_WIDTH = 1280
    SLIDE_HEIGHT = 720
    GAP = 24
    PADDING_X = 24
    PADDING_Y = 16
    TITLE_FONT_SIZE = 28
    FOOTER_FONT_SIZE = 12

    @dataclass
    class Slide:
        title: str
        chair: str
        course: str
        presenter: str
        logo_url: _Optional[str]
        page_number: int
        layout_type: str = "side-by-side"
        subtitle: _Optional[str] = None
        content1: _Optional[mo.core.MIME] = None
        content2: _Optional[mo.core.MIME] = None

        def _header(self) -> mo.core.MIME:
            safe_title = _html.escape(self.title)
            return mo.Html(
                f"""
                <div class="slide-header">
                  <div class="slide-title" style="font-size: {TITLE_FONT_SIZE}px; font-weight: 700; line-height: 1.2; margin: 0;">{safe_title}</div>
                  <div class="slide-hr" style="height: 1px; background: #E5E7EB; margin: 8px 0;"></div>
                </div>
                """
            )

        def _footer(self) -> mo.core.MIME:
            safe_page = _html.escape(str(self.page_number))
            safe_chair = _html.escape(self.chair)
            left_html = f"Seite {safe_page} &nbsp;&nbsp;|&nbsp;&nbsp; {safe_chair}"
            center_img = (
                f'<img class="slide-logo" src="{_html.escape(self.logo_url)}" alt="logo" style="display: block; max-height: 28px; max-width: 160px; margin: 0 auto; object-fit: contain;">'
                if self.logo_url else "&nbsp;"
            )
            return mo.Html(
                f"""
                <div class="slide-footer">
                  <div class="slide-hr" style="height: 1px; background: #E5E7EB; margin: 8px 0;"></div>
                  <div class="slide-footer-row" style="display: grid; grid-template-columns: 1fr auto 1fr; align-items: center;">
                    <div class="slide-footer-left" style="font-size: {FOOTER_FONT_SIZE}px; color: #6B7280; white-space: nowrap;">{left_html}</div>
                    <div class="slide-footer-center">{center_img}</div>
                    <div class="slide-footer-right">&nbsp;</div>
                  </div>
                </div>
                """
            )

        def _title_layout(self) -> mo.core.MIME:
            safe_title = _html.escape(self.title)
            sub = f'<div class="title-slide-sub" style="font-size: 40px; margin: 0 0 16px 0; color: #374151;">{_html.escape(self.subtitle)}</div>' if self.subtitle else ""
            body = mo.Html(
                f"""
                <div class="slide-body title-center" style="flex: 1 1 auto; min-height: 0; display: flex; align-items: center; justify-content: center; height: 100%;">
                  <div class="title-stack" style="text-align: center;">
                    <div class="title-slide-title" style="font-size: 50px; font-weight: 800; margin: 0 0 8px 0;">{safe_title}</div>
                    {sub}
                    <div class="title-slide-meta" style="font-size: 30px; color: #6B7280;">{_html.escape(self.course)}</div>
                    <div class="title-slide-meta" style="font-size: 22px; color: #6B7280;">{_html.escape(self.presenter)}</div>
                  </div>
                </div>
                """
            )
            return mo.Html(
                f"""
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden; page-break-after: always; break-after: page;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                """
            )

        def _one_column_layout(self) -> mo.core.MIME:
            content = mo.md(self.content1) if isinstance(self.content1, str) else (self.content1 or mo.md(""))
            content_wrapped = mo.vstack([content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
            body = mo.Html(
                f"""
                <div class="slide-body" style="flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;">
                    <div class="slide-col tight-md" style="min-height: 0; overflow: auto; padding-right: 2px;">
                        <style>
                            ul {{ margin-top: -0.2em !important; }}
                            .slide-col.tight-md .paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                            .slide-col.tight-md span.paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                            li {{ font-size: 19px !important; }}
                            li * {{ font-size: 19px !important; }}
                        </style>
                        {content_wrapped}
                    </div>
                </div>
                """
            )
            return mo.Html(
                f"""
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden; page-break-after: always; break-after: page;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                """
            )

        def _side_by_side_layout(self) -> mo.core.MIME:
            left_content = mo.md(self.content1) if isinstance(self.content1, str) else (self.content1 or mo.md(""))
            right_content = mo.md(self.content2) if isinstance(self.content2, str) else (self.content2 or mo.md(""))
            left = mo.vstack([left_content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
            right = mo.vstack([right_content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
            body = mo.Html(
                f"""
                <div class="slide-body" style="flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;">
                    <style>
                        ul {{ margin-top: -0.2em !important; }}
                        .slide-col.tight-md .paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                        .slide-col.tight-md span.paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                        li {{ font-size: 19px !important; }}
                        li * {{ font-size: 19px !important; }}
                    </style>
                    <div class="slide-cols" style="display: grid; grid-template-columns: 1fr 1fr; gap: {GAP}px; height: 100%; min-height: 0;">
                        <div class="slide-col tight-md" style="min-height: 0; overflow: auto; padding-right: 2px;">
                            {left}
                        </div>
                        <div class="slide-col tight-md" style="min-height: 0; overflow: auto; padding-right: 2px;">
                            {right}
                        </div>
                    </div>
                </div>
                """
            )
            return mo.Html(
                f"""
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden; page-break-after: always; break-after: page;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                """
            )

        def render(self) -> mo.core.MIME:
            if self.layout_type == "title":
                return self._title_layout()
            elif self.layout_type == "1-column":
                return self._one_column_layout()
            return self._side_by_side_layout()

    class SlideCreator:
        def __init__(self, chair: str, course: str, presenter: str, logo_url: _Optional[str] = None):
            self.chair = chair
            self.course = course
            self.presenter = presenter
            self.logo_url = logo_url
            self._page_counter = 0

        def styles(self) -> mo.core.MIME:
            return mo.Html(
                f"""
                <style>
                  :root {{
                    --slide-w: {SLIDE_WIDTH}px;
                    --slide-h: {SLIDE_HEIGHT}px;
                    --gap: {GAP}px;
                    --pad-x: {PADDING_X}px;
                    --pad-y: {PADDING_Y}px;
                    --title-size: {TITLE_FONT_SIZE}px;
                    --footer-size: {FOOTER_FONT_SIZE}px;
                    --border-color: #E5E7EB;
                    --text-muted: #6B7280;
                    --bg: #ffffff;
                  }}
                  div.slide, .slide {{
                    width: var(--slide-w) !important;
                    height: var(--slide-h) !important;
                    min-width: var(--slide-w) !important;
                    min-height: var(--slide-h) !important;
                    max-width: var(--slide-w) !important;
                    max-height: var(--slide-h) !important;
                    box-sizing: border-box !important;
                    background: var(--bg) !important;
                    padding: var(--pad-y) var(--pad-x) !important;
                    display: flex !important;
                    flex-direction: column !important;
                    border-radius: 6px;
                    box-shadow: 0 0 0 1px #f3f4f6;
                    overflow: hidden !important;
                  }}
                  div.slide-title, .slide-title {{
                    font-size: var(--title-size) !important;
                    font-weight: 700 !important;
                    line-height: 1.2 !important;
                    margin: 0 !important;
                  }}
                  div.slide-hr, .slide-hr {{
                    height: 1px !important;
                    background: var(--border-color) !important;
                    margin: 8px 0 !important;
                  }}
                  div.slide-body, .slide-body {{
                    flex: 1 1 auto !important;
                    min-height: 0 !important;
                    display: flex !important;
                    flex-direction: column !important;
                  }}
                  div.slide-cols, .slide-cols {{
                    display: grid !important;
                    grid-template-columns: 1fr 1fr !important;
                    gap: var(--gap) !important;
                    height: 100% !important;
                    min-height: 0 !important;
                  }}
                  div.slide-col, .slide-col {{
                    min-height: 0 !important;
                    overflow: auto !important;
                    padding-right: 2px !important;
                  }}
                  div.slide-footer div.slide-footer-row, .slide-footer .slide-footer-row {{
                    display: grid !important;
                    grid-template-columns: 1fr auto 1fr !important;
                    align-items: center !important;
                  }}
                  div.slide-footer-left, .slide-footer-left {{
                    font-size: var(--footer-size) !important;
                    color: var(--text-muted) !important;
                    white-space: nowrap !important;
                  }}
                  img.slide-logo, .slide-logo {{
                    display: block !important;
                    max-height: 28px !important;
                    max-width: 160px !important;
                    margin: 0 auto !important;
                    object-fit: contain !important;
                  }}
                  div.title-center, .title-center {{
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    height: 100% !important;
                  }}
                  div.title-stack, .title-stack {{
                    text-align: center !important;
                  }}
                  div.title-slide-title, .title-slide-title {{
                    font-size: 40px !important;
                    font-weight: 800 !important;
                    margin: 0 0 8px 0 !important;
                  }}
                  div.title-slide-sub, .title-slide-sub {{
                    font-size: 20px !important;
                    margin: 0 0 16px 0 !important;
                    color: #374151 !important;
                  }}
                  div.title-slide-meta, .title-slide-meta {{
                    font-size: 16px !important;
                    color: var(--text-muted) !important;
                  }}
                  .tight-md p {{ margin: 0 0 4px 0 !important; }}
                  .tight-md .paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; display: block !important; font-size: 19px !important; }}
                  .tight-md span.paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; display: block !important; font-size: 19px !important; }}
                  ul {{ margin-top: -0.2em !important; margin-bottom: 6px !important; margin-left: 1.25em !important; margin-right: 0 !important; }}
                  .tight-md li {{ margin: 2px 0 !important; font-size: 19px !important; }}
                  li {{ font-size: 19px !important; }}
                  li * {{ font-size: 19px !important; }}
                  .tight-md h1, .tight-md h2, .tight-md h3, .tight-md h4 {{ margin: 0 0 6px 0 !important; }}
                </style>
                """
            )

        def create_slide(self, title: str, layout_type: str = "side-by-side", page_number: _Optional[int] = None) -> Slide:
            if page_number is None:
                self._page_counter += 1
                page_number = self._page_counter
            return Slide(
                title=title,
                chair=self.chair,
                course=self.course,
                presenter=self.presenter,
                logo_url=self.logo_url,
                page_number=page_number,
                layout_type=layout_type,
            )

        def create_title_slide(self, title: str, subtitle: _Optional[str] = None, page_number: _Optional[int] = None) -> Slide:
            slide = self.create_slide(title, layout_type="title", page_number=page_number)
            slide.subtitle = subtitle
            return slide
    return (SlideCreator,)


@app.cell(hide_code=True)
def _(SlideCreator):
    lehrstuhl = "Lehrstuhl für Logistik und Quantitative Methoden"
    vorlesung = "Einführung in die Wirtschaftswissenschaft · IT & Operations"
    presenter = "Richard Pibernik"
    sc = SlideCreator(lehrstuhl, vorlesung, presenter)

    # Farben wie in den Vorlesungsfolien
    NAVY = "#00246C"
    BLUE = "#0074AE"
    PURPLE = "#6A50A1"
    GRAY = "#7A8699"
    ORANGE = "#B56E1F"
    WUE = (49.7913, 9.9534)  # Würzburg, Residenz

    def tag(text, color):
        return (
            f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            f'background:{color};color:white;font-size:14px;font-weight:600;">{text}</span>'
        )

    def kpi(value, label, color=NAVY):
        return (
            f'<div style="padding:10px 14px;border-radius:8px;background:#F4F6F9;'
            f'border-top:4px solid {color};margin-bottom:10px;">'
            f'<div style="font-size:30px;font-weight:700;color:{color};line-height:1.1;">{value}</div>'
            f'<div style="font-size:15px;color:#516078;">{label}</div></div>'
        )

    def fmt(n):
        return f"{n:,.0f}".replace(",", ".")

    return BLUE, GRAY, NAVY, ORANGE, PURPLE, WUE, fmt, kpi, sc, tag


@app.cell(hide_code=True)
def _(sc):
    titleSlide = sc.create_title_slide(
        "Wo bauen wir die nächsten Schnellladeparks?",
        subtitle="Wie Operations und Wirtschaftsinformatik gemeinsam ein echtes Problem lösen",
    )
    sc.styles()
    titleSlide.render()
    return


@app.cell(hide_code=True)
def _(BLUE, PURPLE, mo, sc, tag):
    questionSlide = sc.create_slide("Die Fragestellung", layout_type="side-by-side", page_number=2)
    questionSlide.content1 = mo.md(
        """
        Ein Betreiber von Ladeparks will **k neue Schnellladeparks** bauen
        (Ladeleistung ab 150 kW).

        **Sein Ziel:** Möglichst viele Menschen sollen einen Schnelllader
        in höchstens **R km** Entfernung (Luftlinie) haben.

        Dafür muss er drei Fragen beantworten:

        - Wo gibt es heute **schon** Schnelllader?
        - Wo **wohnen** die Menschen?
        - Wo bringt ein neuer Park den **größten Zusatznutzen**?

        Wir lösen das Problem mit **echten Daten** – in vier Schritten.
        """
    )

    def _step(n, title, text, label, color):
        return (
            f'<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:16px;">'
            f'<div style="flex:0 0 38px;height:38px;border-radius:50%;background:{color};color:white;'
            f'font-weight:700;font-size:18px;display:flex;align-items:center;justify-content:center;">{n}</div>'
            f'<div><div style="font-size:19px;font-weight:700;color:#1A2232;">{title} &nbsp;{tag(label, color)}</div>'
            f'<div style="font-size:16px;color:#516078;">{text}</div></div></div>'
        )

    questionSlide.content2 = mo.Html(
        '<div style="padding:18px 8px;">'
        + _step(1, "Daten beschaffen", "Ladesäulenregister der Bundesnetzagentur, Zensus 2022", "WI", PURPLE)
        + _step(2, "Daten bereinigen und verknüpfen", "Formate, Fehler, zwei Quellen zusammenführen", "WI", PURPLE)
        + _step(3, "Versorgung messen", "Wie viele Menschen haben einen Schnelllader in der Nähe?", "Operations", BLUE)
        + _step(4, "Standorte optimieren", "Optimierungsmodell: Wo bringen k neue Parks am meisten?", "Operations", BLUE)
        + "</div>"
    )
    questionSlide.render()
    return


@app.cell(hide_code=True)
def _(DATA_DIR, pd):
    # ---- Rohdaten laden ----
    raw = pd.read_parquet(str(DATA_DIR / "ladesaeulenregister_2026-09-01.parquet"))
    pop1 = pd.read_parquet(str(DATA_DIR / "zensus2022_bevoelkerung_1km.parquet"))
    try:
        raw_head = (DATA_DIR / "ladesaeulenregister_kopf.txt").read_text(encoding="utf-8")
    except Exception:
        import urllib.request as _ur

        raw_head = _ur.urlopen(str(DATA_DIR / "ladesaeulenregister_kopf.txt")).read().decode("utf-8")
    return pop1, raw, raw_head


@app.cell(hide_code=True)
def _(PURPLE, fmt, mo, pop1, raw, raw_head, sc, tag):
    from html import escape as _escape

    dataSlide = sc.create_slide("Schritt 1: Daten beschaffen", layout_type="side-by-side", page_number=3)
    dataSlide.content1 = mo.md(
        f"""
        {tag("Wirtschaftsinformatik", PURPLE)}

        **Wo stehen die Ladesäulen?**
        Das **Ladesäulenregister** der Bundesnetzagentur ist frei verfügbar
        (Stand 01.09.2026):

        - {fmt(len(raw))} Ladeeinrichtungen, 47 Spalten, 55 MB
        - Betreiber, Adresse, Koordinaten, Leistung je Ladepunkt

        **Wo wohnen die Menschen?**
        Der **Zensus 2022** zählt die Einwohner in einem Gitter aus
        1 × 1 km großen Zellen:

        - {fmt(len(pop1))} bewohnte Zellen, zusammen {fmt(pop1.einwohner.sum())} Einwohner

        Rechts: So sehen die **Rohdaten** aus, wenn man die Datei öffnet.
        """
    )
    dataSlide.content2 = mo.Html(
        '<div style="font-size:13px;color:#516078;margin-bottom:6px;">Die ersten Zeilen der CSV-Datei (gekürzt)</div>'
        '<div style="font-family:Menlo,Consolas,monospace;font-size:10.5px;line-height:1.45;background:#F4F6F9;'
        'border:1px solid #C4D2E3;border-radius:6px;padding:10px;overflow:auto;max-height:540px;">'
        + "".join(
            f'<div style="white-space:nowrap;">{_escape(_l[:95]) or "&nbsp;"}{"…" if len(_l) > 95 else ""}</div>'
            for _l in raw_head.splitlines()
        )
        + "</div>"
    )
    dataSlide.render()
    return


@app.cell(hide_code=True)
def _(np, pd, raw):
    # ---- Bereinigung: naiv vs. sorgfältig ----
    PLUG_COLS = [f"Nennleistung Stecker{i}" for i in range(1, 7)]

    def naive_numbers(s):
        # "einfach umwandeln": Komma -> Punkt, alles andere wird zu NaN
        return pd.to_numeric(s.str.replace(",", "."), errors="coerce")

    def careful_numbers(s):
        # Zellen wie "150; 150" enthalten mehrere Werte (mehrere Stecker an einem Ladepunkt)
        def _max(v):
            if not isinstance(v, str) or not v.strip():
                return np.nan
            return max(float(x.strip().replace(",", ".")) for x in v.split(";"))

        return s.apply(_max)

    df = raw.copy()
    df["lat"] = naive_numbers(df["Breitengrad"])
    df["lon"] = naive_numbers(df["Längengrad"])
    df["n_lp"] = pd.to_numeric(df["Anzahl Ladepunkte"])

    P_naive = pd.concat([naive_numbers(df[c]) for c in PLUG_COLS], axis=1)
    P_clean = pd.concat([careful_numbers(df[c]) for c in PLUG_COLS], axis=1)

    multi_cells = int(sum(df[c].str.contains(";", na=False).sum() for c in PLUG_COLS))
    listed = P_clean.notna().sum(axis=1)
    more_than_6 = int((df.n_lp > 6).sum())

    hpc_naive = (P_naive >= 150).sum(axis=1)
    hpc_clean = (P_clean >= 150).sum(axis=1)
    # Einrichtungen mit > 6 Ladepunkten: nur 6 Spalten vorhanden -> Anzahl übernehmen, wenn alle gelisteten >= 150 kW
    hpc_clean = np.where((df.n_lp > 6) & (hpc_clean == listed) & (listed > 0), df.n_lp, hpc_clean)

    in_de = df.lat.between(47.2, 55.1) & df.lon.between(5.8, 15.1)
    outside = df.loc[~in_de, ["Ort", "Breitengrad", "Längengrad"]]

    df["lp_hpc_naive"] = hpc_naive
    df["lp_hpc"] = hpc_clean
    df["p_max"] = P_clean.max(axis=1)
    df["jahr"] = pd.to_numeric(df["Inbetriebnahmedatum"].str[-4:], errors="coerce")
    stations = df[in_de].copy()

    quality = dict(
        multi_cells=multi_cells,
        more_than_6=more_than_6,
        outside=outside,
        hpc_naive=int(df.lp_hpc_naive.sum()),
        hpc_clean=int(stations.lp_hpc.sum()),
    )
    return quality, stations


@app.cell(hide_code=True)
def _(mo):
    clean_switch = mo.ui.switch(value=False, label="Bereinigung anwenden")
    return (clean_switch,)


@app.cell(hide_code=True)
def _(NAVY, ORANGE, PURPLE, clean_switch, fmt, kpi, mo, quality, sc, tag):
    cleanSlide = sc.create_slide("Schritt 2: Daten bereinigen", layout_type="side-by-side", page_number=4)
    _out = quality["outside"]
    _ex = "; ".join(
        f'{r["Ort"]}: {r["Breitengrad"]}° N, {r["Längengrad"]}° O' for _, r in _out.drop_duplicates().iterrows()
    )
    _outside_txt = (
        f"**{len(_out)} Einrichtungen mit falschen Koordinaten** außerhalb Deutschlands ({_ex})"
        if len(_out)
        else "Keine Koordinaten außerhalb Deutschlands"
    )
    cleanSlide.content1 = mo.md(
        f"""
        {tag("Wirtschaftsinformatik", PURPLE)}

        Echte Daten sind nie sauber. Beim Einlesen fallen auf:

        - **10 Kopfzeilen** vor der eigentlichen Tabelle, Trennzeichen „;“
        - **Dezimalkomma** statt Punkt (z. B. „49,79“)
        - **{fmt(quality["multi_cells"])} Zellen mit mehreren Werten** wie „150; 150“
          (ein Ladepunkt mit zwei Steckern)
        - {_outside_txt}
        - Gemeldet ist nur, wer das **Anzeigeverfahren abgeschlossen** hat –
          die letzten Monate sind unvollständig

        Probieren Sie es aus: Wie viele Schnellladepunkte zählen wir **ohne** und **mit** Bereinigung?
        """
    )
    _val = quality["hpc_clean"] if clean_switch.value else quality["hpc_naive"]
    _col = NAVY if clean_switch.value else ORANGE
    _diff = quality["hpc_clean"] - quality["hpc_naive"]
    cleanSlide.content2 = mo.vstack(
        [
            clean_switch,
            mo.Html(
                kpi(fmt(_val), "Ladepunkte mit mindestens 150 kW", _col)
                + (
                    f'<div style="font-size:17px;color:#1A2232;">Ohne Bereinigung fehlen '
                    f'<b>{fmt(_diff)} Schnellladepunkte</b> – jede Auswertung danach wäre falsch.</div>'
                    if clean_switch.value
                    else '<div style="font-size:17px;color:#516078;">Naiv eingelesen: Werte wie „150; 150“ werden zu „unbekannt“.</div>'
                )
            ),
        ],
        gap=1,
    )
    cleanSlide.render()
    return


@app.cell(hide_code=True)
def _(alt, pd, stations):
    # ---- Ausbau über die Zeit ----
    def _klasse(r):
        if r.lp_hpc > 0:
            return "Schnellladen ab 150 kW"
        if r["Art der Ladeeinrichtung"] == "Schnellladeeinrichtung" or (r.p_max or 0) > 22:
            return "Schnellladen unter 150 kW"
        return "Normalladen (bis 22 kW)"

    _s = stations[stations.jahr.between(2015, 2026)].copy()
    _s["klasse"] = _s.apply(_klasse, axis=1)
    # Ladepunkte zählen (bei Schnellladern ab 150 kW nur diese Punkte)
    _s["lp"] = _s.apply(lambda r: r.lp_hpc if r.lp_hpc > 0 else r.n_lp, axis=1)
    growth = _s.groupby(["jahr", "klasse"]).lp.sum().reset_index()
    growth["jahr"] = growth.jahr.astype(int).astype(str)
    growth_chart = (
        alt.Chart(growth)
        .mark_bar()
        .encode(
            x=alt.X("jahr:N", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("lp:Q", title="Neue Ladepunkte pro Jahr"),
            color=alt.Color(
                "klasse:N",
                title=None,
                scale=alt.Scale(
                    domain=["Normalladen (bis 22 kW)", "Schnellladen unter 150 kW", "Schnellladen ab 150 kW"],
                    range=["#C4D2E3", "#7FA7CF", "#00246C"],
                ),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=["jahr", "klasse", alt.Tooltip("lp:Q", format=",.0f")],
        )
        .properties(width=560, height=380)
    )
    hpc_by_year = growth[growth.klasse == "Schnellladen ab 150 kW"].set_index("jahr").lp
    return growth_chart, hpc_by_year


@app.cell(hide_code=True)
def _(fmt, growth_chart, hpc_by_year, mo, sc, stations):
    growthSlide = sc.create_slide("Was die Daten zeigen: der Ausbau", layout_type="side-by-side", page_number=5)
    growthSlide.content1 = mo.md(
        f"""
        Nach der Bereinigung können wir auswerten:

        - Insgesamt **{fmt(stations.n_lp.sum())} öffentliche Ladepunkte**,
          davon **{fmt(stations.lp_hpc.sum())}** mit mindestens 150 kW
        - Neue Schnellladepunkte ab 150 kW:
          {fmt(hpc_by_year.get("2021", 0))} (2021) → {fmt(hpc_by_year.get("2023", 0))} (2023)
          → {fmt(hpc_by_year.get("2025", 0))} (2025)
        - Beim Normalladen sinkt der Zubau seit 2023 –
          der Ausbau verschiebt sich zum **schnellen Laden**

        2026 ist noch unvollständig (Stand September, Meldeverzug).
        """
    )
    growthSlide.content2 = growth_chart
    growthSlide.render()
    return


@app.cell(hide_code=True)
def _(np, stations):
    # ---- Schnelllade-Standorte bilden (Ladeeinrichtungen am selben Ort zusammenfassen) ----
    _h = stations[stations.lp_hpc > 0].copy()
    _h["key"] = _h.lat.round(3).astype(str) + "," + _h.lon.round(3).astype(str)
    hpc_sites = (
        _h.groupby("key")
        .agg(
            lat=("lat", "mean"),
            lon=("lon", "mean"),
            lp=("lp_hpc", "sum"),
            kw=("p_max", "max"),
            betreiber=("Betreiber", "first"),
            ort=("Ort", "first"),
        )
        .reset_index(drop=True)
    )

    EARTH_R = 6371.0

    def to_xyz(lat, lon):
        # Kugelkoordinaten -> 3D (km); für kurze Strecken entspricht der Abstand der Luftlinie
        la, lo = np.radians(lat), np.radians(lon)
        return np.column_stack([EARTH_R * np.cos(la) * np.cos(lo), EARTH_R * np.cos(la) * np.sin(lo), EARTH_R * np.sin(la)])

    return hpc_sites, to_xyz


@app.cell(hide_code=True)
def _(NAVY, folium, fmt, hpc_sites, mo, sc):
    _m = folium.Map(location=[51.1, 10.4], zoom_start=6, tiles="OpenStreetMap", prefer_canvas=True)
    for _r in hpc_sites.itertuples():
        folium.CircleMarker(
            location=[_r.lat, _r.lon],
            radius=1.5 + min(_r.lp, 40) ** 0.5,
            color=NAVY,
            weight=0,
            fill=True,
            fill_opacity=0.55,
            tooltip=f"{_r.ort}: {_r.lp} Ladepunkte ({_r.betreiber})",
        ).add_to(_m)
    mapSlide = sc.create_slide(
        f"Wo stehen heute Schnelllader? {fmt(len(hpc_sites))} Standorte mit {fmt(hpc_sites.lp.sum())} Ladepunkten",
        layout_type="1-column",
        page_number=6,
    )
    mapSlide.content1 = mo.iframe(_m.get_root().render(), height="560px")
    mapSlide.render()
    return


@app.cell(hide_code=True)
def _(cKDTree, hpc_sites, np, pop1, stations, to_xyz):
    # ---- Verknüpfung: Abstand jeder Gitterzelle zum nächsten Schnelllader ----
    hpc_tree = cKDTree(to_xyz(hpc_sites.lat.values, hpc_sites.lon.values))
    pop = pop1.copy()
    pop_xyz = to_xyz(pop.lat.values, pop.lon.values)
    pop["d_km"] = hpc_tree.query(pop_xyz)[0]
    # Ortsnamen für spätere Standortvorschläge: nächste Ladeeinrichtung
    _st = stations.dropna(subset=["lat", "lon"])
    name_tree = cKDTree(to_xyz(_st.lat.values, _st.lon.values))
    name_list = _st["Ort"].values
    return name_list, name_tree, pop


@app.cell(hide_code=True)
def _(mo):
    radius = mo.ui.slider(start=2, stop=20, step=1, value=5, show_value=True, label="Entfernung R (km)")
    region = mo.ui.dropdown(
        options=["Umkreis Würzburg (60 km)", "Deutschland"],
        value="Umkreis Würzburg (60 km)",
        label="Gebiet",
    )
    return radius, region


@app.cell(hide_code=True)
def _(WUE, np, pop, region, to_xyz):
    if region.value == "Deutschland":
        pop_reg = pop
    else:
        _w = to_xyz(np.array([WUE[0]]), np.array([WUE[1]]))[0]
        _d = np.linalg.norm(to_xyz(pop.lat.values, pop.lon.values) - _w, axis=1)
        pop_reg = pop[_d <= 60]
    return (pop_reg,)


@app.cell(hide_code=True)
def _(alt, hpc_sites, np, pd, pop_reg, radius):
    # Versorgungsgrad je Entfernung
    _tot = pop_reg.einwohner.sum()
    cov_curve = pd.DataFrame(
        {
            "R": np.arange(1, 21),
            "anteil": [(pop_reg.einwohner * (pop_reg.d_km <= r)).sum() / _tot for r in range(1, 21)],
        }
    )
    _base = alt.Chart(cov_curve).encode(
        x=alt.X("R:Q", title="Entfernung R (km)"),
        y=alt.Y("anteil:Q", title="Anteil der Bevölkerung", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
    )
    cov_chart = (
        _base.mark_line(color="#0074AE", strokeWidth=3)
        + _base.mark_point(color="#0074AE", filled=True).encode(tooltip=["R", alt.Tooltip("anteil:Q", format=".1%")])
        + alt.Chart(pd.DataFrame({"R": [radius.value]})).mark_rule(color="#B56E1F", strokeDash=[4, 4]).encode(x="R:Q")
    ).properties(width=480, height=200)

    covered_share = (pop_reg.einwohner * (pop_reg.d_km <= radius.value)).sum() / _tot
    uncovered_pop = int((pop_reg.einwohner * (pop_reg.d_km > radius.value)).sum())

    # Karte: 5-km-Zellen, eingefärbt nach Versorgung
    _G = 5000
    _p = pop_reg.assign(gx=(pop_reg.x // _G), gy=(pop_reg.y // _G), unc=pop_reg.einwohner * (pop_reg.d_km > radius.value))
    _g = (
        _p.groupby(["gx", "gy"])
        .apply(
            lambda d: pd.Series(
                {"lat": np.average(d.lat, weights=d.einwohner), "lon": np.average(d.lon, weights=d.einwohner),
                 "einwohner": d.einwohner.sum(), "ohne": d.unc.sum()}
            ),
            include_groups=False,
        )
        .reset_index()
    )
    _g["status"] = np.where(_g.ohne > 0.5 * _g.einwohner, "ohne Schnelllader", "versorgt")
    _span_km = (pop_reg.lat.max() - pop_reg.lat.min()) * 111
    _px = 470 / _span_km * 5  # Kantenlänge einer 5-km-Zelle in Pixeln
    cov_map = (
        alt.Chart(_g)
        .mark_square(size=max(4, _px**2 * 0.9))
        .encode(
            longitude="lon:Q",
            latitude="lat:Q",
            opacity=alt.Opacity("einwohner:Q", scale=alt.Scale(type="log", range=[0.25, 1]), legend=None),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(domain=["versorgt", "ohne Schnelllader"], range=["#C4D2E3", "#B56E1F"]),
                legend=alt.Legend(orient="top", title=None),
            ),
            tooltip=[alt.Tooltip("einwohner:Q", format=",.0f"), alt.Tooltip("ohne:Q", format=",.0f", title="ohne Schnelllader")],
        )
    )
    _c_lat, _c_lon = pop_reg.lat.mean(), pop_reg.lon.mean()
    _r_km = max((pop_reg.lat.max() - pop_reg.lat.min()), (pop_reg.lon.max() - pop_reg.lon.min()) * 0.65) * 111 / 2
    _dd = np.hypot((hpc_sites.lat - _c_lat) * 111, (hpc_sites.lon - _c_lon) * 111 * np.cos(np.radians(_c_lat)))
    _hs = hpc_sites[_dd <= _r_km] if _r_km < 200 else hpc_sites
    _sites_layer = (
        alt.Chart(_hs.assign(typ="Schnelllader heute"))
        .mark_circle(size=18, opacity=0.95)
        .encode(
            longitude="lon:Q",
            latitude="lat:Q",
            color=alt.Color("typ:N", scale=alt.Scale(domain=["Schnelllader heute"], range=["#00246C"]), legend=alt.Legend(orient="top", title=None)),
            tooltip=["ort:N", "lp:Q"],
        )
    )
    cov_map = (
        alt.layer(cov_map, _sites_layer)
        .resolve_scale(color="independent")
        .project("mercator")
        .properties(width=520, height=470)
    )
    return cov_chart, cov_map, covered_share, uncovered_pop


@app.cell(hide_code=True)
def _(
    BLUE,
    ORANGE,
    cov_chart,
    cov_map,
    covered_share,
    fmt,
    kpi,
    mo,
    radius,
    region,
    sc,
    tag,
    uncovered_pop,
):
    coverSlide = sc.create_slide("Schritt 3: Wie gut ist die Versorgung?", layout_type="side-by-side", page_number=7)
    coverSlide.content1 = mo.vstack(
        [
            mo.md(tag("Operations", BLUE)),
            mo.md("Wir verknüpfen beide Datenquellen: Für jede Gitterzelle berechnen wir die Entfernung zum nächsten Schnelllader."),
            mo.hstack([region, radius], justify="start", gap=2),
            mo.hstack(
                [
                    mo.Html(kpi(f"{covered_share:.1%}".replace(".", ","), f"der Menschen haben einen Schnelllader in ≤ {radius.value} km", BLUE)),
                    mo.Html(kpi(fmt(uncovered_pop), "Menschen ohne Schnelllader in der Nähe", ORANGE)),
                ],
                widths=[1, 1],
                gap=1,
            ),
            cov_chart,
        ],
        gap=0.6,
    )
    coverSlide.content2 = cov_map
    coverSlide.render()
    return


@app.cell(hide_code=True)
def _(BLUE, mo, sc, tag):
    modelSlide = sc.create_slide("Schritt 4: Das Optimierungsmodell", layout_type="side-by-side", page_number=8)
    modelSlide.content1 = mo.md(
        f"""
        {tag("Operations", BLUE)}

        **In Worten:** Wähle aus vielen möglichen Orten genau **k** aus,
        sodass möglichst viele bisher **unversorgte Menschen** einen
        neuen Park in höchstens **R km** Entfernung haben.

        Das ist ein klassisches Modell der Standortplanung:
        das **Maximal Covering Location Problem**.

        Mögliche Standorte und Nachfrage: alle 5 × 5 km großen Gebiete,
        in denen heute Menschen ohne Schnelllader in der Nähe wohnen.

        Ein Rechner (Solver) findet die **beste** Kombination –
        bei 10.000 möglichen Orten gibt es mehr Kombinationen,
        als man je ausprobieren könnte.
        """
    )
    modelSlide.content2 = mo.md(
        r"""
        **Entscheidungen**

        - $y_j = 1$, wenn wir am Ort $j$ einen Park bauen
        - $z_i = 1$, wenn Gebiet $i$ danach versorgt ist

        **Ziel:** möglichst viele Menschen $w_i$ versorgen

        $$\max \sum_i w_i \, z_i$$

        **Nebenbedingungen**

        $$z_i \le \sum_{j \,:\, d_{ij} \le R} y_j \quad \text{für alle Gebiete } i$$

        $$\sum_j y_j = k$$

        $$y_j \in \{0,1\}, \quad 0 \le z_i \le 1$$
        """
    )
    modelSlide.render()
    return


@app.cell(hide_code=True)
def _(mo):
    k_slider = mo.ui.slider(start=1, stop=30, step=1, value=5, show_value=True, label="Neue Parks k")
    run_btn = mo.ui.run_button(label="Optimieren")
    return k_slider, run_btn


@app.cell(hide_code=True)
def _(
    Bounds,
    LinearConstraint,
    cKDTree,
    coo_matrix,
    csr_matrix,
    milp,
    np,
    pd,
    pop_reg,
    radius,
    sp_hstack,
    to_xyz,
):
    # ---- Daten für das Modell: unversorgte Bevölkerung auf 5-km-Gebiete verdichten ----
    _G = 5000
    _u = pop_reg[pop_reg.d_km > radius.value]
    _u = _u.assign(gx=_u.x // _G, gy=_u.y // _G)
    areas = (
        _u.groupby(["gx", "gy"])
        .apply(
            lambda d: pd.Series(
                {"lat": np.average(d.lat, weights=d.einwohner), "lon": np.average(d.lon, weights=d.einwohner), "w": d.einwohner.sum()}
            ),
            include_groups=False,
        )
        .reset_index()
    )
    _xyz = to_xyz(areas.lat.values, areas.lon.values)
    _tree = cKDTree(_xyz)
    _pairs = _tree.query_ball_point(_xyz, radius.value)
    _rows = np.concatenate([np.array(p, dtype=int) for p in _pairs]) if len(_pairs) else np.array([], dtype=int)
    _cols = np.concatenate([np.full(len(p), j, dtype=int) for j, p in enumerate(_pairs)]) if len(_pairs) else np.array([], dtype=int)
    n_areas = len(areas)
    cover = coo_matrix((np.ones(len(_rows)), (_rows, _cols)), shape=(n_areas, n_areas)).tocsr()

    def solve_mclp(k):
        """Maximal Covering Location Problem mit scipy/HiGHS."""
        n = n_areas
        if n == 0:
            return np.array([], dtype=int), 0.0
        c = np.concatenate([np.zeros(n), -areas.w.values])
        eye = csr_matrix((np.ones(n), (np.arange(n), np.arange(n))), shape=(n, n))
        A1 = sp_hstack([-cover, eye])
        A2 = sp_hstack([csr_matrix(np.ones((1, n))), csr_matrix((1, n))])
        res = milp(
            c,
            constraints=[LinearConstraint(A1, -np.inf, 0), LinearConstraint(A2, k, k)],
            integrality=np.concatenate([np.ones(n), np.zeros(n)]),
            bounds=Bounds(0, 1),
            options={"time_limit": 60, "mip_rel_gap": 1e-3},
        )
        chosen = np.where(res.x[:n] > 0.5)[0]
        return chosen, -res.fun

    def greedy_curve(kmax):
        """Schnelle Näherung: immer den Ort mit dem größten Zusatznutzen nehmen."""
        w = areas.w.values.astype(float).copy()
        cov_t = cover.T.tocsr()
        out, total = [], 0.0
        for _ in range(kmax):
            gains = cov_t @ w
            j = int(np.argmax(gains))
            if gains[j] <= 0:
                out.append(total)
                continue
            total += gains[j]
            w[cover[:, j].nonzero()[0]] = 0.0
            out.append(total)
        return out

    return areas, greedy_curve, n_areas, solve_mclp


@app.cell(hide_code=True)
def _(areas, k_slider, mo, n_areas, name_list, name_tree, np, region, run_btn, solve_mclp, to_xyz):
    # Im Umkreis Würzburg rechnet der Solver sofort; für ganz Deutschland erst nach Klick (dauert einige Sekunden)
    if region.value == "Deutschland" and not run_btn.value:
        chosen, covered_new = np.array([], dtype=int), None
    else:
        with mo.status.spinner(title="Der Solver rechnet ..."):
            chosen, covered_new = solve_mclp(k_slider.value)
    new_sites = areas.iloc[chosen].copy()
    if len(new_sites):
        _idx = name_tree.query(to_xyz(new_sites.lat.values, new_sites.lon.values))[1]
        new_sites["bei"] = name_list[_idx]
    else:
        new_sites["bei"] = []
    solution = dict(sites=new_sites, covered=covered_new, k=k_slider.value, n=n_areas)
    return (solution,)


@app.cell(hide_code=True)
def _(GRAY, PURPLE, folium, hpc_sites, pop_reg, region, solution):
    _center = [pop_reg.lat.mean(), pop_reg.lon.mean()]
    _m = folium.Map(location=_center, zoom_start=6 if region.value == "Deutschland" else 9, tiles="OpenStreetMap", prefer_canvas=True)
    _lat0, _lat1, _lon0, _lon1 = pop_reg.lat.min(), pop_reg.lat.max(), pop_reg.lon.min(), pop_reg.lon.max()
    for _r in hpc_sites.itertuples():
        if _lat0 <= _r.lat <= _lat1 and _lon0 <= _r.lon <= _lon1:
            folium.CircleMarker(
                location=[_r.lat, _r.lon], radius=3, color=GRAY, weight=0, fill=True, fill_opacity=0.7,
                tooltip=f"bestehend: {_r.ort}, {_r.lp} Ladepunkte",
            ).add_to(_m)
    for _r in solution["sites"].itertuples():
        folium.Marker(
            location=[_r.lat, _r.lon],
            tooltip=f"Neuer Park bei {_r.bei}: +{_r.w:,.0f} Einwohner im Umkreis".replace(",", "."),
            icon=folium.Icon(color="purple", icon="bolt", prefix="fa"),
        ).add_to(_m)
    result_map = _m
    return (result_map,)


@app.cell(hide_code=True)
def _(
    BLUE,
    PURPLE,
    fmt,
    k_slider,
    kpi,
    mo,
    pop_reg,
    radius,
    region,
    result_map,
    run_btn,
    sc,
    solution,
    tag,
    uncovered_pop,
):
    solveSlide = sc.create_slide("Schritt 4: Die optimalen Standorte", layout_type="side-by-side", page_number=9)
    _tot = pop_reg.einwohner.sum()
    _before = _tot - uncovered_pop
    _cov = solution["covered"] or 0
    _after = _before + _cov
    _names = ", ".join(solution["sites"].sort_values("w", ascending=False).bei.head(8))
    solveSlide.content1 = mo.vstack(
        [
            mo.md(tag("Operations", BLUE)),
            mo.md(f"**{region.value}**, Entfernung R = {radius.value} km (Einstellung aus Schritt 3)"),
            mo.hstack([k_slider, run_btn], justify="start", gap=2),
            mo.hstack(
                [
                    mo.Html(
                        kpi("+" + fmt(_cov), f"Menschen zusätzlich versorgt durch {solution['k']} neue Parks", PURPLE)
                        if solution["covered"] is not None
                        else kpi("?", "Für ganz Deutschland bitte auf „Optimieren“ klicken", PURPLE)
                    ),
                    mo.Html(
                        kpi(
                            f"{_before / _tot:.1%} → {_after / _tot:.1%}".replace(".", ","),
                            "Anteil der Bevölkerung mit Schnelllader in der Nähe",
                            BLUE,
                        )
                    ),
                ],
                widths=[1, 1],
                gap=1,
            ),
            mo.md(f"**Neue Parks u. a. bei:** {_names}" if _names else ""),
            mo.md(f"<span style='font-size:14px;color:#7A8699'>{fmt(solution['n'])} mögliche Orte geprüft.</span>"),
        ],
        gap=0.6,
    )
    solveSlide.content2 = mo.iframe(result_map.get_root().render(), height="560px")
    solveSlide.render()
    return


@app.cell(hide_code=True)
def _(alt, greedy_curve, pd, solution):
    _kmax = 30
    _g = greedy_curve(_kmax)
    curve = pd.DataFrame({"k": range(1, _kmax + 1), "versorgt": _g})
    curve["zusatz"] = curve.versorgt.diff().fillna(curve.versorgt)
    _base = alt.Chart(curve).encode(x=alt.X("k:Q", title="Anzahl neuer Parks k", scale=alt.Scale(domain=[0, _kmax + 1])))
    curve_chart = (
        _base.mark_bar(color="#A998D0").encode(y=alt.Y("zusatz:Q", title="Zusätzlich versorgte Menschen je Park"))
        .properties(width=520, height=170)
    )
    total_chart = (
        _base.mark_line(color="#6A50A1", strokeWidth=3).encode(y=alt.Y("versorgt:Q", title="Versorgte Menschen insgesamt"))
        + alt.Chart(pd.DataFrame({"k": [solution["k"]], "v": [solution["covered"] if solution["covered"] is not None else float("nan")]}))
        .mark_point(color="#00246C", size=120, filled=True)
        .encode(x="k:Q", y="v:Q", tooltip=[alt.Tooltip("v:Q", title="Optimum (Solver)", format=",.0f")])
    ).properties(width=520, height=200)
    greedy_at_k = _g[solution["k"] - 1]
    return curve_chart, greedy_at_k, total_chart


@app.cell(hide_code=True)
def _(curve_chart, fmt, greedy_at_k, mo, sc, solution, total_chart):
    marginalSlide = sc.create_slide("Jeder weitere Park bringt weniger", layout_type="side-by-side", page_number=10)
    _gap = (solution["covered"] - greedy_at_k) if solution["covered"] is not None else None
    marginalSlide.content1 = mo.md(
        f"""
        **Abnehmender Grenznutzen:** Die ersten Parks versorgen viele Menschen,
        jeder weitere deutlich weniger – die großen Lücken sind schnell geschlossen,
        übrig bleiben dünn besiedelte Gebiete.

        Für das Management heißt das: **Wie viele Parks lohnen sich?**
        Dafür brauchen wir zusätzlich Kosten und erwartete Einnahmen.

        **Heuristik oder Optimum?** Die Kurve rechts nutzt eine schnelle Faustregel
        (immer den Ort mit dem größten Zusatznutzen nehmen).
        {"" if _gap is None else f'Bei k = {solution["k"]} findet der Solver ' + ("genau dieselbe Lösung" if abs(_gap) < 1 else f"<b>{fmt(_gap)} Menschen mehr</b>") + " (blauer Punkt)."}
        """
    )
    marginalSlide.content2 = mo.vstack([total_chart, curve_chart], gap=0.5)
    marginalSlide.render()
    return


@app.cell(hide_code=True)
def _(BLUE, PURPLE, mo, sc, tag):
    wrapSlide = sc.create_slide("Was haben WI und Operations beigetragen?", layout_type="side-by-side", page_number=11)
    wrapSlide.content1 = mo.md(
        f"""
        {tag("Wirtschaftsinformatik", PURPLE)}

        - Passende **Datenquellen** finden und beschaffen
        - Daten **verstehen und bereinigen** – sonst fehlen 1.500 Schnellladepunkte
        - Zwei Quellen **verknüpfen** (Ladesäulen + Zensus-Gitter)
        - Das Ganze als **Werkzeug** bereitstellen, das andere bedienen können

        {tag("Operations", BLUE)}

        - Das Problem **strukturieren**: Ziel, Entscheidungen, Annahmen
        - **Messen**, wie gut die Versorgung heute ist
        - Ein **Optimierungsmodell** aufstellen und lösen
        - Zielkonflikte zeigen: Wie viele Parks lohnen sich?
        """
    )
    wrapSlide.content2 = mo.md(
        """
        **Was unser Modell (noch) nicht kann**

        - **Luftlinie** statt echter Fahrstrecke
        - **Einwohner** statt echtem Ladebedarf – wer zu Hause lädt,
          braucht seltener einen Schnelllader
        - **Durchreiseverkehr** auf Autobahnen fehlt
        - Wie **groß** muss ein Park sein? Wie lange wartet man?

        Die letzte Frage beantworten wir im nächsten Beispiel:
        **Kapazitätsplanung für einen Schnellladepark an der A3.**

        <span style="font-size:13px;color:#7A8699">Quellen: Bundesnetzagentur, Ladesäulenregister (Stand 01.09.2026);
        Zensus 2022, Bevölkerung im 1-km-Gitter (Statistische Ämter des Bundes und der Länder, dl-de/by-2-0),
        aufbereitet über das Repository jslth/z22data.</span>
        """
    )
    wrapSlide.render()
    return


if __name__ == "__main__":
    app.run()
