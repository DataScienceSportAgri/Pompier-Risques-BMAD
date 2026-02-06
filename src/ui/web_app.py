"""
Application Streamlit — layout et contrôles de base.
Story 2.4.1 : Interface Streamlit (carte centre, colonnes gauche/droite, bandeaux).

Layout : 3 bandes verticales (pas 3 colonnes au départ) :
  1. Ligne très fine (titre) + bandeau contrôles : occupent 1/8 viewport (ligne centrale 1/8 sous barre nav).
  2. Grande ligne centrale : carte Paris + événements (gauche, 90% largeur, rect. même taille que arr.) + arrondissements (droite).
  3. Très fine ligne du bas : Jours, Run, ML training %, Nb jours.
Marges écran : 1/6 gauche, 1/4.5 droite, 1/8 haut, 1/8 bas. Rectangles : texte contenu, pas de débordement.
Charte : pastel, Inter, français.
"""

from __future__ import annotations

import logging
import pickle
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from src.core.config.config_validator import Config, load_and_validate_config
from src.core.utils.path_resolver import PathResolver
from src.services.simulation_service import SimulationService

logger = logging.getLogger(__name__)

# Story 2.4.5.1 — Libellés lisibles pour les 18 features hebdo (nomenclature 2.2.5 / 2.3.1)
FEATURE_LABELS_18: Dict[str, str] = {
    "agressions_moyen_grave": "Agressions moyen+grave",
    "agressions_benin": "Agressions bénin",
    "incendies_moyen_grave": "Incendies moyen+grave",
    "incendies_benin": "Incendies bénin",
    "accidents_moyen_grave": "Accidents moyen+grave",
    "accidents_benin": "Accidents bénin",
    "agressions_alcool": "Agressions alcool",
    "agressions_nuit": "Agressions nuit",
    "incendies_alcool": "Incendies alcool",
    "incendies_nuit": "Incendies nuit",
    "accidents_alcool": "Accidents alcool",
    "accidents_nuit": "Accidents nuit",
    "morts_accidents": "Morts accidents",
    "morts_incendies": "Morts incendies",
    "morts_agressions": "Morts agressions",
    "blesses_graves_accidents": "Blessés graves accidents",
    "blesses_graves_incendies": "Blessés graves incendies",
    "blesses_graves_agressions": "Blessés graves agressions",
}


# --- Configuration page Streamlit ---
st.set_page_config(
    page_title="Simulation Risques Paris",
    page_icon="🚒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Layout 3 bandes : fine ligne haut | grande centrale (carte) | très fine ligne bas
CARTE_IFRAME_HEIGHT = 680

# Ligne centrale 1/8 sous la barre de navigation : les 2 lignes (titre + bandeau) occupent cet espace.
# Marges écran : 1/6 gauche, 1/4.5 droite, 1/8 haut, 1/8 bas (chrome = 1/8).
HAUT_CHROME_VH = 100 / 8  # 12.5vh
TITRE_LIGNE_VH = 1.5
BANDEAU_HAUT_VH = 10
DIVIDER_VH = 0.2
BANDEAU_HAUT_PADDING_TOP = "0.01rem"
BANDEAU_HAUT_PADDING_BOTTOM = "0.01rem"
BANDEAU_HAUT_FONT_SIZE = "0.56rem"
BANDEAU_RADIO_GAP_REM = "2.6rem"
# Écart entre les 2 boutons Prédiction/Entraînement (spacer) — réglable ici, appliqué en CSS
RADIO_OPTIONS_SPACER_REM = "1.6"
# Hauteur du spacer au-dessus de "Type de modèle" (flux Streamlit) pour le caler entre les 2 lignes radio
TYPE_MODELE_SPACER_REM = "1.0"
# Réduction du vide horizontal entre colonne radio et colonne "Type de modèle"
GAP_RADIO_TYPE_REDUCTION_REM = "0.4"

# Grande ligne centrale : événements | carte | arrondissements
# Colonne gauche 1,5× plus large (espace bord écran ↔ carte), rectangles 95% de cette largeur
RATIO_GAUCHE, RATIO_CARTE, RATIO_DROITE = 9, 57, 20
RATIO_PRED, RATIO_REAL, RATIO_ARR = 10, 10, 12

# --- Charte visuelle : Inter, pastel — proportions type PDF "vu" ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
    /* Réduire l'espace entre bandeau navigateur et titre (trop grand espace au-dessus du titre) */
    section[data-testid="stAppViewContainer"] { padding-top: 0 !important; }
    .main .block-container { padding-top: 0 !important; padding-bottom: 0.08rem !important; max-width: 100%%; }
    .main .block-container > div { margin-top: 0 !important; margin-bottom: 0 !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .main .block-container > div:first-child { padding-top: 0 !important; margin-top: 0 !important; }
    /* Bloc 1 : ligne très fine dédiée au titre, collé au haut — pas d'espace au-dessus */
    .main .block-container > div:nth-child(1) { max-height: """ + str(TITRE_LIGNE_VH) + """vh !important; overflow: hidden !important; padding: 0 !important; padding-top: 0 !important; margin: 0 !important; }
    .main .block-container > div:nth-child(1) h3 { font-size: 1rem !important; margin: 0 !important; line-height: 1.2 !important; white-space: nowrap !important; }
    /* Bloc 2 : bandeau contrôles (scénario, variabilité, LANCEMENT, radio, type, modèle, algo) */
    .main .block-container > div:nth-child(2) { max-height: """ + str(BANDEAU_HAUT_VH) + """vh !important; overflow: visible !important; padding-top: """ + BANDEAU_HAUT_PADDING_TOP + """ !important; padding-bottom: """ + BANDEAU_HAUT_PADDING_BOTTOM + """ !important; margin-bottom: 0 !important; }
    .main .block-container > div:nth-child(2) [data-testid="stVerticalBlock"] { gap: 0 !important; min-height: 0 !important; }
    .main .block-container > div:nth-child(2) [data-testid="stSelectbox"] > div { min-height: 1.05rem !important; padding-top: 0.05rem !important; padding-bottom: 0.05rem !important; }
    .main .block-container > div:nth-child(2) [data-testid="stSelectbox"] [data-testid="stSelectboxInput"] { min-height: 1rem !important; }
    /* Radio Prédiction/Entraînement : vertical, gap """ + BANDEAU_RADIO_GAP_REM + """ (aligné avec Modèle / Algo) */
    .main .block-container > div:nth-child(2) [data-testid="stRadio"] > div { flex-direction: column !important; align-items: flex-start !important; gap: """ + BANDEAU_RADIO_GAP_REM + """ !important; row-gap: """ + BANDEAU_RADIO_GAP_REM + """ !important; flex-wrap: nowrap !important; }
    /* Marge entre les 2 options : plusieurs cibles au cas où la structure DOM diffère */
    .main .block-container > div:nth-child(2) [data-testid="stRadio"] div[role="radio"]:first-of-type { margin-bottom: """ + BANDEAU_RADIO_GAP_REM + """ !important; }
    .main .block-container > div:nth-child(2) [data-testid="stRadio"] div[role="radiogroup"] > *:first-child { margin-bottom: """ + BANDEAU_RADIO_GAP_REM + """ !important; }
    .main .block-container > div:nth-child(2) [data-testid="stRadio"] label + label { margin-top: """ + BANDEAU_RADIO_GAP_REM + """ !important; }
    .main [data-testid="stRadio"] label + label { margin-top: """ + BANDEAU_RADIO_GAP_REM + """ !important; }
    .main .block-container > div:nth-child(2) .stButton > button { padding: 0.18rem 0.45rem !important; font-size: 0.58rem !important; }
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] { padding-top: """ + BANDEAU_HAUT_PADDING_TOP + """ !important; padding-bottom: """ + BANDEAU_HAUT_PADDING_BOTTOM + """ !important; min-height: 0 !important; align-items: stretch !important; }
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] label { font-size: """ + BANDEAU_HAUT_FONT_SIZE + """ !important; line-height: 1.1 !important; margin-bottom: 0.05rem !important; }
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] .stSelectbox label { font-size: """ + BANDEAU_HAUT_FONT_SIZE + """ !important; line-height: 1.1 !important; }
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] [data-testid="stRadio"] label { font-size: """ + BANDEAU_HAUT_FONT_SIZE + """ !important; line-height: 1.1 !important; white-space: nowrap !important; }
    /* Colonne radio (6) : forcer plus de largeur ; rapprocher de la colonne Type (diminuer espace) */
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] > div:nth-child(6) { flex: 0 0 18%% !important; min-width: 8rem !important; max-width: 18rem !important; margin-right: -""" + GAP_RADIO_TYPE_REDUCTION_REM + """rem !important; }
    /* Colonne Type de modèle (7) : alignement (spacer dans le flux) ; rapprocher des radios */
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] > div:nth-child(7) { display: flex !important; align-items: flex-start !important; margin-left: -""" + GAP_RADIO_TYPE_REDUCTION_REM + """rem !important; }
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] > div:nth-child(7) > div { display: flex !important; flex-direction: column !important; align-items: flex-start !important; width: 100%%; gap: 0 !important; }
    /* Colonne Modèle + Algorithmes (8) : même gap """ + BANDEAU_RADIO_GAP_REM + """ que radio, alignement hauteur Modèle↔Prédiction et Algo↔Entraînement */
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] > div:nth-child(8) > div { display: flex !important; flex-direction: column !important; gap: """ + BANDEAU_RADIO_GAP_REM + """ !important; justify-content: flex-start !important; align-items: stretch !important; }
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] > div:nth-child(8) [data-testid="stSelectbox"] { margin-top: 0 !important; margin-bottom: 0 !important; padding-top: 0 !important; padding-bottom: 0 !important; }
    .type-modele-spacer { display: block !important; margin: 0 !important; padding: 0 !important; }
    .radio-options-spacer { display: block !important; height: """ + RADIO_OPTIONS_SPACER_REM + """rem !important; margin: 0 !important; padding: 0 !important; line-height: 0 !important; font-size: 0 !important; }
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] > div:nth-child(7) [data-testid="stMarkdown"]:first-of-type { margin-top: 0 !important; margin-bottom: 0 !important; padding: 0 !important; }
    /* Boutons Prédiction/Entraînement (col 6) : style radio, pas LANCEMENT */
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] > div:nth-child(6) .stButton > button { justify-content: flex-start !important; width: 100%% !important; background: transparent !important; color: inherit !important; box-shadow: none !important; border: none !important; font-size: """ + BANDEAU_HAUT_FONT_SIZE + """ !important; padding: 0.1rem 0 !important; }
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] > div:nth-child(6) .stButton > button:hover { background: rgba(0,0,0,0.05) !important; }
    .main .block-container > div:nth-child(2) [data-testid="stHorizontalBlock"] > div:nth-child(6) [data-testid="stMarkdown"] { margin-top: 0 !important; margin-bottom: 0 !important; padding: 0 !important; }
    /* Bloc 3 : divider — fine */
    .main .block-container > div:nth-child(3) { max-height: """ + str(DIVIDER_VH) + """vh !important; margin: 0.02rem 0 !important; padding: 0 !important; }
    .main .block-container > div:nth-child(3) hr { margin: 0.02rem 0 !important; }
    .main h1, .main h3 { font-size: 1rem; margin-top: 0; margin-bottom: 0; }
    .main p[data-testid="stCaptionContainer"] { margin-top: 0 !important; margin-bottom: 0.03rem !important; }
    .main hr { margin-top: 0.03rem !important; margin-bottom: 0.03rem !important; }
    /* Bloc 4 : grande ligne centrale (carte + événements + arrondissements) */
    .main .block-container > div:nth-child(4) { margin-top: 0 !important; padding-top: 0 !important; flex: 1 !important; }
    /* Rectangles événements et arrondissements : même taille, texte contenu (pas de débordement ni redimensionnement) */
    .pastel-box {
        background: linear-gradient(135deg, #e8f4f8 0%%, #f0e6fa 100%%);
        border-radius: 6px;
        padding: 0.2rem 0.35rem;
        margin: 0.08rem 0;
        border: 1px solid #c9d6e3;
        text-align: center;
        font-weight: 500;
        font-size: 0.7rem;
        line-height: 1.2;
        min-height: 1.6rem;
        box-sizing: border-box;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 100%%;
    }
    .pastel-box-roman { font-size: 0.68rem; }
    .event-grave { border-left: 3px solid #c62828; }
    .event-normal { border-left: 3px solid #2e7d32; }
    /* Colonne événements : rectangles sur 95% de l'espace (bord gauche écran → carte) */
    .events-rectangles { width: 95%; max-width: 95%; box-sizing: border-box; }
    .events-rectangles .pastel-box { width: 100%; }
    .bandeau-bas { background: #e8f4f8; padding: 0.15rem 0.4rem; border-radius: 4px; margin-top: 0.1rem; border-top: 1px solid #c9d6e3; font-size: 0.78rem; }
    /* Bandeau bas : ligne fine (1/55) */
    section.main [data-testid="stVerticalBlock"] > div:last-of-type { padding-top: 0.06rem !important; }
    section.main [data-testid="stVerticalBlock"] > div:last-of-type [data-testid="stHorizontalBlock"] { margin-top: 0 !important; min-height: 0 !important; }
    section.main [data-testid="stVerticalBlock"] > div:last-of-type .stSlider { padding-top: 0 !important; padding-bottom: 0 !important; }
    section.main [data-testid="stVerticalBlock"] > div:last-of-type .stSlider > div { height: 1.1rem !important; }
    section.main [data-testid="stVerticalBlock"] > div:last-of-type label { font-size: 0.72rem !important; margin-bottom: 0 !important; }
    section.main [data-testid="stVerticalBlock"] > div:last-of-type [data-testid="stCaptionContainer"] { padding: 0 !important; min-height: 0 !important; }
    section.main [data-testid="stVerticalBlock"] > div:last-of-type [data-testid="stNumberInput"] { padding: 0 !important; }
    section.main [data-testid="stVerticalBlock"] > div:last-of-type [data-testid="stNumberInput"] input { height: 1.35rem !important; font-size: 0.78rem !important; }
    .zone-carte { min-height: """ + str(CARTE_IFRAME_HEIGHT) + """px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_microzones() -> Optional[gpd.GeoDataFrame]:
    """Charge les microzones depuis data/source_data/microzones.pkl (Epic 1). Rend les géométries valides pour l'affichage."""
    path = PathResolver.data_source("microzones.pkl")
    if not path.exists():
        return None
    with open(path, "rb") as f:
        data = pickle.load(f)
    if isinstance(data, dict) and "data" in data:
        gdf = data["data"].copy()
    else:
        gdf = data.copy()
    if not isinstance(gdf, gpd.GeoDataFrame):
        return None
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    # Rendre les géométries valides pour que Folium affiche toutes les microzones
    if hasattr(gdf.geometry, "make_valid"):
        gdf["geometry"] = gdf.geometry.make_valid()
    else:
        # Shapely 1.x : buffer(0) pour corriger certaines invalidités
        gdf["geometry"] = gdf.geometry.buffer(0)
    # Réindexer pour un __geo_interface__ propre (éviter trous dans les features)
    gdf = gdf.reset_index(drop=True)
    return gdf


def load_locations_casernes_hopitaux() -> Optional[pd.DataFrame]:
    """
    Charge les positions casernes et hôpitaux depuis data/source_data/locations_casernes_hopitaux.pkl.
    Story 2.4.3.5 — Colonnes attendues : nom, type (caserne | hopital), microzone.
    Retourne None si fichier absent ou invalide (log warning).
    """
    path = PathResolver.data_source("locations_casernes_hopitaux.pkl")
    if not path.exists():
        logger.warning("locations_casernes_hopitaux.pkl non trouvé : %s", path)
        return None
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        if hasattr(data, "columns") and hasattr(data, "iterrows"):
            return data.copy()
        if isinstance(data, dict) and "data" in data:
            return pd.DataFrame(data["data"])
        if isinstance(data, (list, tuple)):
            return pd.DataFrame(data)
        logger.warning("Format locations_casernes_hopitaux.pkl inattendu : %s", type(data))
        return None
    except Exception as e:
        logger.warning("Chargement locations_casernes_hopitaux.pkl : %s", e)
        return None


def build_events_column_html(
    active_events: List[Tuple[str, str, bool]],
    incidents_graves: List[Tuple[str, str]],
) -> str:
    """Construit le HTML de la colonne Événements (gauche) avec rectangles stables et tooltip unique.
    La zone de survol est calculée sur le rectangle ; seule la bulle d'info est mise à jour au fil des jours."""
    style = (
        ".pastel-box{background:linear-gradient(135deg,#e8f4f8 0%,#f0e6fa 100%);border-radius:6px;padding:0.2rem 0.35rem;"
        "margin:0.08rem 0;border:1px solid #c9d6e3;text-align:center;font-weight:500;font-size:0.7rem;}"
        ".event-grave{border-left:3px solid #c62828;}.event-normal{border-left:3px solid #2e7d32;}"
    )
    parts = [
        "<style>" + style + "</style>",
        '<div class="events-rectangles" style="width:95%;max-width:95%;">',
        '<div id="events-tt" style="display:none;position:fixed;z-index:99999;max-width:240px;padding:0.3rem 0.4rem;'
        'background:#2d3748;color:#fff;font-size:0.65rem;line-height:1.3;border-radius:4px;'
        'pointer-events:none;white-space:pre-wrap;box-shadow:0 2px 8px rgba(0,0,0,0.3);"></div>',
    ]
    for label, tooltip, is_grave in active_events:
        cls = "event-grave" if is_grave else "event-normal"
        tip_esc = tooltip.replace('"', "&quot;").replace("<", "&lt;").replace("\n", " ")
        parts.append(
            f'<div class="pastel-box events-box {cls}" data-tip="{tip_esc}" '
            'style="min-height:1.6rem;cursor:pointer;">' + label + "</div>"
        )
    for label, tooltip in incidents_graves:
        tip_esc = tooltip.replace('"', "&quot;").replace("<", "&lt;").replace("\n", " ")
        parts.append(
            f'<div class="pastel-box event-grave events-box" data-tip="{tip_esc}" '
            'style="min-height:1.6rem;cursor:pointer;">' + label + "</div>"
        )
    if not active_events and not incidents_graves:
        parts.append('<div class="pastel-box events-box" data-tip="">—</div>')
    parts.append("</div>")
    script = r"""
<script>
(function() {
  var tt = document.getElementById('events-tt');
  var boxes = document.querySelectorAll('.events-box');
  function showTip(e, content) {
    if (!tt) return;
    tt.innerHTML = (content || '').replace(/\n/g, '<br/>');
    tt.style.display = content ? 'block' : 'none';
    tt.style.left = (e.clientX + 12) + 'px';
    tt.style.top = (e.clientY + 12) + 'px';
  }
  function hideTip() { if (tt) tt.style.display = 'none'; }
  function moveTip(e) {
    if (tt && tt.style.display === 'block') {
      tt.style.left = (e.clientX + 12) + 'px';
      tt.style.top = (e.clientY + 12) + 'px';
    }
  }
  boxes.forEach(function(b) {
    b.addEventListener('mouseenter', function(e) {
      var tip = (b.getAttribute('data-tip') || '').replace(/&quot;/g, '"').replace(/&lt;/g, '<');
      showTip(e, tip);
    });
    b.addEventListener('mousemove', moveTip);
    b.addEventListener('mouseleave', hideTip);
  });
})();
</script>
"""
    return "".join(parts) + script


def build_arrondissements_column_html(
    totaux: Dict[int, Dict[str, Any]],
    jour_actuel: int,
) -> str:
    """Construit le HTML de la colonne Arrondissements (droite) avec rectangles et bulle tooltip dynamique.
    Chaque rectangle a data-tip avec les stats précises (accident/agression/incendie bénin/moyen/grave, nuit, alcool)."""
    style = (
        ".pastel-box{background:linear-gradient(135deg,#e8f4f8 0%,#f0e6fa 100%);border-radius:6px;padding:0.2rem 0.35rem;"
        "margin:0.08rem 0;border:1px solid #c9d6e3;text-align:center;font-weight:500;font-size:0.7rem;}"
        ".pastel-box-roman{font-variant-numeric:tabular-nums;}"
    )
    default_data = {
        "accident": (0, 0, 0, 0),
        "agression": (0, 0, 0, 0),
        "incendie": (0, 0, 0, 0),
        "alcool": _default_alcool_nuit(),
        "nuit": _default_alcool_nuit(),
    }
    parts = [
        "<style>" + style + "</style>",
        '<div class="arrondissements-rectangles" style="width:100%;">',
        '<div id="arr-tt" style="display:none;position:fixed;z-index:99999;max-width:260px;padding:0.35rem 0.5rem;'
        'background:#2d3748;color:#fff;font-size:0.65rem;line-height:1.35;border-radius:4px;'
        'pointer-events:none;white-space:pre-wrap;box-shadow:0 2px 8px rgba(0,0,0,0.3);"></div>',
    ]
    for arr in range(1, 21):
        data = totaux.get(arr, default_data)
        acc_t, ag_t, inc_t = data["accident"][0], data["agression"][0], data["incendie"][0]
        line = f"🚗💥 {acc_t}  🔪 {ag_t}  🔥 {inc_t}"
        acc_b, acc_m, acc_g = data["accident"][1], data["accident"][2], data["accident"][3]
        agr_b, agr_m, agr_g = data["agression"][1], data["agression"][2], data["agression"][3]
        inc_b, inc_m, inc_g = data["incendie"][1], data["incendie"][2], data["incendie"][3]
        nuit_line, alcool_line = _format_alcool_nuit_tooltip(
            data.get("alcool", _default_alcool_nuit()),
            data.get("nuit", _default_alcool_nuit()),
        )
        tooltip_lines = [
            f"Accident : {acc_b} bénins, {acc_m} moyen, {acc_g} grave",
            f"Agression : {agr_b} bénins, {agr_m} moyen, {agr_g} grave",
            f"Incendie : {inc_b} bénins, {inc_m} moyen, {inc_g} grave",
            nuit_line,
            alcool_line,
        ]
        tip_text = "\n".join(tooltip_lines)
        tip_esc = tip_text.replace('"', "&quot;").replace("<", "&lt;").replace("\n", " ")
        roman = arrondissement_roman(arr)
        parts.append(
            f'<div class="pastel-box arr-box" data-tip="{tip_esc}" '
            f'style="min-height:1.8rem;cursor:pointer;"><span class="pastel-box-roman">{roman}</span><br/>{line}</div>'
        )
    parts.append("</div>")
    script = r"""
<script>
(function() {
  var tt = document.getElementById('arr-tt');
  var boxes = document.querySelectorAll('.arr-box');
  function showTip(e, content) {
    if (!tt) return;
    tt.innerHTML = (content || '').replace(/\n/g, '<br/>');
    tt.style.display = content ? 'block' : 'none';
    tt.style.left = (e.clientX + 12) + 'px';
    tt.style.top = (e.clientY + 12) + 'px';
  }
  function hideTip() { if (tt) tt.style.display = 'none'; }
  function moveTip(e) {
    if (tt && tt.style.display === 'block') {
      tt.style.left = (e.clientX + 12) + 'px';
      tt.style.top = (e.clientY + 12) + 'px';
    }
  }
  boxes.forEach(function(b) {
    b.addEventListener('mouseenter', function(e) {
      var tip = (b.getAttribute('data-tip') || '').replace(/&quot;/g, '"').replace(/&lt;/g, '<');
      showTip(e, tip);
    });
    b.addEventListener('mousemove', moveTip);
    b.addEventListener('mouseleave', hideTip);
  });
})();
</script>
"""
    return "".join(parts) + script


def wrap_map_html(map_html: str, save_view_to_url: bool = True) -> str:
    """Enveloppe le HTML de la carte pour remplir tout l'iframe.
    Si save_view_to_url=True, injecte un script qui enregistre centre et zoom dans l'URL à chaque pan/zoom (debounce)."""
    if not save_view_to_url:
        return (
            '<div style="width:100%; height:100%; margin:0; padding:0; overflow:hidden; box-sizing:border-box;">'
            f'<div style="width:100%; height:100%;">{map_html}</div></div>'
        )
    script = r"""
<script>
(function() {
  var debounceTimer;
  var STORAGE_KEY = 'bmad_map_view';
  function findMap() {
    try {
      if (typeof L === 'undefined') return null;
      var el = document.querySelector('.folium-map');
      if (el && L.Map && L.Map._instances && el._leaflet_id != null)
        return L.Map._instances[el._leaflet_id] || null;
      for (var k in window) {
        try {
          var o = window[k];
          if (o && typeof o.getCenter === 'function' && typeof o.getZoom === 'function' && typeof o.on === 'function')
            return o;
        } catch (e) {}
      }
    } catch (e) {}
    return null;
  }
  function saveView(c) {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({lat: c.lat, lng: c.lng, zoom: c.zoom}));
      }
    } catch (e) {}
  }
  function captureView() {
    var map = findMap();
    if (!map) return;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function() {
      try {
        var c = map.getCenter();
        var z = map.getZoom();
        saveView({lat: c.lat, lng: c.lng, zoom: z});
        var url = new URL(window.top.location.href);
        url.searchParams.set('map_lat', Math.round(c.lat * 1e6) / 1e6);
        url.searchParams.set('map_lng', Math.round(c.lng * 1e6) / 1e6);
        url.searchParams.set('map_zoom', z);
        if (window.top.history && window.top.history.replaceState) {
          window.top.history.replaceState({}, '', url.toString());
        } else {
          window.top.location = url.toString();
        }
      } catch (e) {}
    }, 600);
  }
  function restoreView() {
    try {
      var map = findMap();
      if (!map || typeof localStorage === 'undefined') return;
      var s = localStorage.getItem(STORAGE_KEY);
      if (s) {
        var v = JSON.parse(s);
        if (v.lat != null && v.lng != null && v.zoom != null) {
          map.setView([v.lat, v.lng], v.zoom);
        }
      }
    } catch (e) {}
  }
  setTimeout(function() {
    var map = findMap();
    if (map) {
      restoreView();
      map.on('moveend', captureView);
      map.on('zoomend', captureView);
    }
  }, 50);
})();
</script>
"""
    return (
        '<div style="width:100%; height:100%; margin:0; padding:0; overflow:hidden; box-sizing:border-box;">'
        f'<div style="width:100%; height:100%;">{map_html}</div>{script}</div>'
    )


# Tailles emoji par gravité (px) — Story 2.4.3 : bénin 20, moyen 27, grave 34
SIZE_PX_BENIN, SIZE_PX_MOYEN, SIZE_PX_GRAVE = 20, 27, 34
# Décalage aléatoire autour du centre de la microzone (degrés ~quelques pixels)
EVENT_MARKER_OFFSET_DEG = 0.0002


def _gravite_to_size_px(gravite: str) -> int:
    """Retourne la taille en pixels selon la gravité (benin, moyen, grave)."""
    g = (gravite or "benin").lower()
    if g == "grave":
        return SIZE_PX_GRAVE
    if g == "moyen":
        return SIZE_PX_MOYEN
    return SIZE_PX_BENIN


def _event_emoji_html(event_type: str, gravite: str) -> str:
    """Retourne le HTML pour un marqueur emoji (taille selon gravité). Agression 🔪, Incendie 🔥, Accident 🚗💥 côte à côte."""
    size_px = _gravite_to_size_px(gravite)
    style = f"font-size:{size_px}px;line-height:1;display:inline-block;"
    t = (event_type or "").lower().replace("_grave", "").strip()
    if t == "agression":
        return f'<span style="{style}">🔪</span>'
    if t == "incendie":
        return f'<span style="{style}">🔥</span>'
    if t == "accident":
        return f'<span style="{style}">🚗</span><span style="{style}">💥</span>'
    return f'<span style="{style}">•</span>'


def _centroid_with_random_offset(
    microzones: gpd.GeoDataFrame,
    microzone_id: str,
    max_offset_deg: float = EVENT_MARKER_OFFSET_DEG,
) -> Optional[Tuple[float, float]]:
    """Retourne (lat, lon) = centre de la microzone + décalage aléatoire en degrés, ou None si microzone introuvable."""
    col = "microzone_id" if "microzone_id" in microzones.columns else None
    if col is None:
        return None
    row = microzones[microzones[col] == microzone_id]
    if row.empty:
        return None
    geom = row.iloc[0].geometry
    if geom is None:
        return None
    try:
        c = geom.centroid
        lat, lon = float(c.y), float(c.x)
        lat += random.uniform(-max_offset_deg, max_offset_deg)
        lon += random.uniform(-max_offset_deg, max_offset_deg)
        return (lat, lon)
    except Exception:
        return None


def _centroid_from_microzone(
    microzones: gpd.GeoDataFrame,
    microzone_id: str,
) -> Optional[Tuple[float, float]]:
    """Retourne (lat, lon) = centroïde exact de la microzone, ou None si introuvable. Story 2.4.3.5."""
    col = "microzone_id" if "microzone_id" in microzones.columns else None
    if col is None:
        return None
    row = microzones[microzones[col] == microzone_id]
    if row.empty:
        return None
    geom = row.iloc[0].geometry
    if geom is None:
        return None
    try:
        c = geom.centroid
        return (float(c.y), float(c.x))
    except Exception:
        return None


def _add_casernes_hopitaux_markers(
    m: folium.Map,
    microzones: gpd.GeoDataFrame,
    df_locations: pd.DataFrame,
) -> None:
    """Ajoute les marqueurs casernes (🚒) et hôpitaux (🏥) sur la carte. Story 2.4.3.5."""
    for _, row in df_locations.iterrows():
        mz_id = row.get("microzone")
        if not mz_id:
            continue
        coords = _centroid_from_microzone(microzones, str(mz_id))
        if coords is None:
            continue
        lat, lon = coords
        type_ = (row.get("type") or "").strip().lower()
        emoji = "🚒" if type_ == "caserne" else "🏥"
        nom = str(row.get("nom", "")).strip() or "—"
        icon = folium.DivIcon(
            html=f'<div style="font-size:1.2rem;line-height:1;">{emoji}</div>',
            icon_size=(28, 28),
            icon_anchor=(14, 14),
        )
        folium.Marker(
            location=[lat, lon],
            icon=icon,
            tooltip=nom,
        ).add_to(m)


def _add_event_markers(
    m: folium.Map,
    microzones: gpd.GeoDataFrame,
    events: List[Any],
) -> None:
    """Ajoute sur la carte des marqueurs emoji pour chaque événement (agression 🔪, incendie 🔥, accident 🚗💥), répartis autour du centre de la microzone."""
    for ev in events:
        microzone_id = ev.get("microzone_id") if isinstance(ev, dict) else getattr(ev, "microzone_id", None)
        event_type = ev.get("type") if isinstance(ev, dict) else getattr(ev, "type", None)
        gravite = ev.get("gravite") if isinstance(ev, dict) else getattr(ev, "gravite", "benin")
        if not microzone_id:
            continue
        coords = _centroid_with_random_offset(microzones, microzone_id)
        if coords is None:
            continue
        lat, lon = coords
        size_px = _gravite_to_size_px(gravite)
        is_accident = (event_type or "").lower().replace("_grave", "") == "accident"
        w, h = (size_px * 2 + 4, size_px + 4) if is_accident else (size_px + 4, size_px + 4)
        html = _event_emoji_html(event_type or "", gravite)
        icon = folium.DivIcon(
            html=f'<div style="display:inline-flex;align-items:center;justify-content:center;">{html}</div>',
            icon_size=(w, h),
            icon_anchor=(w // 2, h // 2),
        )
        folium.Marker(location=[lat, lon], icon=icon).add_to(m)


def _microzone_colors_from_events(events: List[Any]) -> Dict[str, dict]:
    """Priorité Feu > Agression > Accident. Feu: jaune/orange/rouge. Agression: dégradé marron. Accident: dégradé gris."""
    # mz_id -> (priorité_type 1=incendie 2=agression 3=accident, grav_order 0=benin 1=moyen 2=grave, grav label)
    mz_best: Dict[str, Tuple[int, int, str]] = {}
    for ev in events:
        mz_id = ev.get("microzone_id") if isinstance(ev, dict) else getattr(ev, "microzone_id", None)
        if not mz_id:
            continue
        t = (ev.get("type") if isinstance(ev, dict) else getattr(ev, "type", None) or "").lower().replace("_grave", "")
        g = (ev.get("gravite") if isinstance(ev, dict) else getattr(ev, "gravite", "benin") or "benin").lower()
        if t == "incendie":
            prio = 1
        elif t == "agression":
            prio = 2
        elif t == "accident":
            prio = 3
        else:
            continue
        grav_order = ("benin", "moyen", "grave").index(g) if g in ("benin", "moyen", "grave") else 0
        cur = mz_best.get(mz_id)
        if cur is None or prio < cur[0] or (prio == cur[0] and grav_order > cur[1]):
            mz_best[mz_id] = (prio, grav_order, g)
    out: Dict[str, dict] = {}
    for mz_id, (prio, _, grav) in mz_best.items():
        if prio == 1:  # Feu : dégradé jaune / orange / rouge
            fill = "#c62828" if grav == "grave" else "#f57c00" if grav == "moyen" else "#fbc02d"
        elif prio == 2:  # Agression : dégradé marron (clair → foncé)
            fill = "#4e342e" if grav == "grave" else "#8d6e63" if grav == "moyen" else "#bcaaa4"
        else:  # Accident : dégradé gris (clair → foncé)
            fill = "#424242" if grav == "grave" else "#757575" if grav == "moyen" else "#bdbdbd"
        out[mz_id] = {"fillColor": fill, "color": "#333", "weight": 1.5, "fillOpacity": 0.7}
    return out


def build_map_paris(
    microzones: gpd.GeoDataFrame,
    events: Optional[List[Any]] = None,
    state: Optional[Any] = None,
    jour: Optional[int] = None,
    location: Optional[Tuple[float, float]] = None,
    zoom_start: Optional[int] = None,
    show_casernes_hopitaux: bool = False,
    df_locations: Optional[pd.DataFrame] = None,
) -> folium.Map:
    """Construit une carte Folium centrée sur Paris avec microzones, événements (🔪🔥🚗💥) et optionnellement casernes (🚒) et hôpitaux (🏥).
    events : liste de dict ou objets avec microzone_id, type, gravite. Si state et jour sont fournis, le tooltip microzone affiche les 3 vecteurs du jour.
    show_casernes_hopitaux : si True et df_locations fourni, ajoute les marqueurs casernes/hôpitaux. Story 2.4.3.5.
    location et zoom_start : pour conserver le même cadrage entre mises à jour."""
    center = location or (48.8566, 2.3522)
    zoom = zoom_start if zoom_start is not None else 12
    m = folium.Map(location=list(center), zoom_start=zoom, tiles="CartoDB positron")
    mz_colors = _microzone_colors_from_events(events or [])
    id_col = "microzone_id" if "microzone_id" in microzones.columns else None

    # Préparer GeoDataFrame pour le tooltip : au survol d'une microzone, afficher les 3 vecteurs du jour (accident, incendie, agression) si state + jour fournis
    gdf = microzones.copy()
    vecteurs_par_mz = get_vecteurs_tooltip_par_microzone(state, jour or 0) if state is not None and jour is not None else {}
    if vecteurs_par_mz and id_col and id_col in gdf.columns:
        gdf["_accident"] = gdf[id_col].map(
            lambda mz_id: f"accident {vecteurs_par_mz.get(mz_id, {}).get('accident', '(0, 0, 0)')}"
        )
        gdf["_incendie"] = gdf[id_col].map(
            lambda mz_id: f"incendie {vecteurs_par_mz.get(mz_id, {}).get('incendie', '(0, 0, 0)')}"
        )
        gdf["_agression"] = gdf[id_col].map(
            lambda mz_id: f"agression {vecteurs_par_mz.get(mz_id, {}).get('agression', '(0, 0, 0)')}"
        )
        tooltip_cols = ["_accident", "_incendie", "_agression"]
        tooltip_aliases = ["accident", "incendie", "agression"]
    else:
        tooltip_cols = [c for c in gdf.columns if c != "geometry"][:5]
        tooltip_aliases = tooltip_cols

    def style_fn(feature: dict) -> dict:
        default = {"fillColor": "#a8d4e6", "color": "#3d7a94", "weight": 1, "fillOpacity": 0.5}
        if id_col and feature.get("properties"):
            mz_id = feature["properties"].get(id_col)
            if mz_id and mz_id in mz_colors:
                return {**default, **mz_colors[mz_id]}
        return default

    folium.GeoJson(
        gdf.__geo_interface__,
        name="Microzones",
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_cols,
            aliases=tooltip_aliases,
        ) if tooltip_cols else None,
    ).add_to(m)
    if events:
        _add_event_markers(m, microzones, events)
    if show_casernes_hopitaux and df_locations is not None and not df_locations.empty:
        _add_casernes_hopitaux_markers(m, microzones, df_locations)
    # Ne pas appeler fit_bounds si location/zoom fournis (conserver le cadrage entre mises à jour)
    if location is None and zoom_start is None:
        try:
            bounds = microzones.total_bounds  # minx, miny, maxx, maxy (WGS84)
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], max_zoom=14)
        except Exception:
            pass
    return m


def get_vecteurs_tooltip_par_microzone(
    state: Optional[Any],
    jour: int,
) -> Dict[str, Dict[str, str]]:
    """
    Retourne pour chaque microzone les 3 vecteurs du jour (accident, incendie, agression)
    au format (grave, moyen, bénin) pour affichage dans le tooltip au survol de la carte.
    """
    out: Dict[str, Dict[str, str]] = {}
    if state is None:
        return out
    try:
        vs = state.vectors_state
        for mz_id in vs.get_all_microzones():
            vectors_mz = vs.get_vectors_for_day(mz_id, jour) or {}
            vec_str: Dict[str, str] = {}
            for name in ("accident", "incendie", "agression"):
                vec = vectors_mz.get(name)
                if vec is not None:
                    vec_str[name] = f"({vec.grave}, {vec.moyen}, {vec.benin})"
                else:
                    vec_str[name] = "(0, 0, 0)"
            out[mz_id] = vec_str
    except Exception as e:
        logger.warning("get_vecteurs_tooltip_par_microzone: %s", e)
    return out


def build_map_events_from_state(state: Any, jour: int) -> List[dict]:
    """Construit la liste d'événements pour la carte à partir du SimulationState (vecteurs du jour)."""
    events: List[dict] = []
    try:
        vs = state.vectors_state
        for mz_id in vs.get_all_microzones():
            vectors_mz = vs.get_vectors_for_day(mz_id, jour)
            for inc_type, vec in (vectors_mz or {}).items():
                if vec is None:
                    continue
                for _ in range(vec.benin):
                    events.append({"microzone_id": mz_id, "type": inc_type, "gravite": "benin"})
                for _ in range(vec.moyen):
                    events.append({"microzone_id": mz_id, "type": inc_type, "gravite": "moyen"})
                for _ in range(vec.grave):
                    events.append({"microzone_id": mz_id, "type": inc_type, "gravite": "grave"})
    except Exception as e:
        logger.warning("build_map_events_from_state: %s", e)
    return events


def arrondissement_label(arr: int) -> str:
    """Libellé français : 1er, 2e, … 20e."""
    if arr == 1:
        return "1er"
    return f"{arr}e"


def arrondissement_roman(arr: int) -> str:
    """Chiffres romains I … XX."""
    romans = (
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
        "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
    )
    if 1 <= arr <= 20:
        return romans[arr - 1]
    return str(arr)


def microzone_to_arrondissement(microzone_id: str) -> int:
    """Extrait l'arrondissement depuis microzone_id. Fallback si pas de fichier limites.
    Formats supportés : MZ_11_01 → 11 ; MZ031 (MZ + 3 chiffres, 5 microzones/arr) → 7."""
    try:
        parts = microzone_id.split("_")
        if len(parts) >= 2:
            return max(1, min(20, int(parts[1])))
        # Format MZxxx (ex. MZ031) : 5 microzones par arrondissement (MZ001-005→1, MZ031-035→7)
        if (
            isinstance(microzone_id, str)
            and len(microzone_id) == 5
            and microzone_id.startswith("MZ")
            and microzone_id[2:].isdigit()
        ):
            idx = int(microzone_id[2:])
            return max(1, min(20, (idx - 1) // 5 + 1))
    except (ValueError, TypeError):
        pass
    return 1


# Cache du mapping microzone_id → arrondissement (limites_microzone_arrondissement.pkl)
_limites_microzone_arrondissement: Optional[Dict[str, int]] = None


def get_limites_microzone_arrondissement() -> Optional[Dict[str, int]]:
    """Charge une fois le mapping microzone_id → arrondissement (1..20) depuis data/source_data."""
    global _limites_microzone_arrondissement
    if _limites_microzone_arrondissement is not None:
        return _limites_microzone_arrondissement
    try:
        from src.services.casualty_calculator import CasualtyCalculator
        _limites_microzone_arrondissement = CasualtyCalculator.load_limites_microzone_arrondissement()
        return _limites_microzone_arrondissement
    except (FileNotFoundError, ValueError, Exception):
        return None


def microzone_to_arrondissement_mapped(microzone_id: str) -> int:
    """Arrondissement pour une microzone : utilise limites_microzone_arrondissement.pkl si dispo, sinon parse (MZ_XX_YY ou MZxxx)."""
    limites = get_limites_microzone_arrondissement()
    if limites is not None:
        arr = limites.get(microzone_id)
        if arr is not None and 1 <= arr <= 20:
            return arr
    return microzone_to_arrondissement(microzone_id)


def _get_casualty_calculator_for_details() -> Tuple[Optional[Any], Optional[str]]:
    """
    Construit CasualtyCalculator avec GoldenHourCalculator pour le détail morts/blessés.
    Story 2.4.5.2 — Retourne (calculator, None) ou (None, message_erreur).
    """
    try:
        from src.core.golden_hour import CaserneManager, GoldenHourCalculator
        from src.services.casualty_calculator import CasualtyCalculator

        distances_cm, distances_mh, temps_base_cm, temps_base_mh = GoldenHourCalculator.load_trajets()
        caserne_ids = list(distances_cm.keys())
        caserne_manager = CaserneManager(caserne_ids, seed=0)
        gh = GoldenHourCalculator(
            caserne_manager,
            distances_cm,
            distances_mh,
            temps_base_cm,
            temps_base_mh,
            seed=0,
        )
        limites = CasualtyCalculator.load_limites_microzone_arrondissement()
        cc = CasualtyCalculator(gh, limites, seed=0)
        return (cc, None)
    except FileNotFoundError as e:
        return (None, str(e))
    except Exception as e:
        logger.warning("_get_casualty_calculator_for_details: %s", e)
        return (None, str(e))


def _collect_casualties_jour(state: Any, jour: int) -> Tuple[List[Dict], List[Dict]]:
    """
    Collecte les morts et blessés graves (tous arrondissements, dont le 1) pour un jour avec détail Golden Hour.
    Story 2.4.5.2. Retourne (list_morts, list_blesses_graves) à étendre.
    """
    cc, err = _get_casualty_calculator_for_details()
    if cc is None:
        return ([], [])
    try:
        _, _, list_morts, list_blesses = cc.calculer_casualties_jour_avec_details(
            jour,
            state.vectors_state,
            state.events_state,
            is_nuit=None,
            is_alcool=None,
        )
        return (list_morts, list_blesses)
    except Exception as e:
        logger.warning("_collect_casualties_jour(jour=%s): %s", jour, e)
        return ([], [])


def _get_features_18_semaine_derniere(state: Any, jour_actuel: int) -> Optional[Any]:
    """
    Calcule les 18 features hebdomadaires pour la **semaine dernière** (semaine complète écoulée).
    Story 2.4.5.1 — Source : SimulationState + StateCalculator, ou features précalculées (run_XXX/ml/features.pkl).
    Semaine dernière : J1–J7 → sem 1, J8–J14 → sem 2, etc. (affichable dès jour_actuel >= 7).
    """
    if state is None or jour_actuel < 7:
        return None
    # Semaine dernière (dernière semaine complète) : J7 → sem 1, J8–J14 → sem 1, J15 → sem 2
    semaine_derniere = (jour_actuel - 7) // 7 + 1
    run_id = getattr(state, "run_id", "run_000")
    run_num = run_id.replace("run_", "")

    # 1) Calcul à la volée depuis state (limites + StateCalculator)
    limites = get_limites_microzone_arrondissement()
    if limites and len(limites) > 0:
        try:
            from src.services.casualty_calculator import CasualtyCalculator
            from src.services.feature_calculator import StateCalculator

            cc = CasualtyCalculator(limites)
            fc = StateCalculator(limites, casualty_calculator=cc)
            df = fc.calculer_features_semaine(
                semaine_derniere,
                state.vectors_state,
                state.dynamic_state,
                state.events_state,
            )
            if df is not None and not df.empty:
                return df
        except Exception as e:
            logger.warning("_get_features_18_semaine_derniere (calcul à la volée): %s", e)

    # 2) Fallback : features précalculées (run_XXX/ml/features.pkl) si extraction ML déjà faite
    try:
        from src.services.feature_calculator import StateCalculator

        df_all = StateCalculator.load_features(run_num)
        if df_all is not None and not df_all.empty and "semaine" in df_all.columns:
            df_week = df_all[df_all["semaine"] == semaine_derniere]
            if not df_week.empty:
                return df_week
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning("_get_features_18_semaine_derniere (fallback features.pkl): %s", e)

    return None


def _feature_90_col_to_readable(col: str) -> str:
    """
    Mapping nom technique 90 features → libellé lisible (Story 2.4.5.1).
    central_sem_m1_* → « Central dernière semaine – … », central_sem_m2_* → « Central semaine -2 – … », etc.
    voisins_moy_sem_m1_* → « Voisins (moyenne) dernière semaine – … »
    """
    suffix_labels = FEATURE_LABELS_18
    if col.startswith("central_sem_m1_"):
        suffix = col.replace("central_sem_m1_", "")
        return "Central dernière semaine – " + suffix_labels.get(suffix, suffix.replace("_", " "))
    if col.startswith("central_sem_m2_"):
        suffix = col.replace("central_sem_m2_", "")
        return "Central semaine -2 – " + suffix_labels.get(suffix, suffix.replace("_", " "))
    if col.startswith("central_sem_m3_"):
        suffix = col.replace("central_sem_m3_", "")
        return "Central semaine -3 – " + suffix_labels.get(suffix, suffix.replace("_", " "))
    if col.startswith("central_sem_m4_"):
        suffix = col.replace("central_sem_m4_", "")
        return "Central semaine -4 – " + suffix_labels.get(suffix, suffix.replace("_", " "))
    if col.startswith("voisins_moy_sem_m1_"):
        suffix = col.replace("voisins_moy_sem_m1_", "")
        return "Voisins (moyenne) dernière semaine – " + suffix_labels.get(suffix, suffix.replace("_", " "))
    return col.replace("_", " ")


def _get_90_features_data(state: Any, mode_ml: str) -> Tuple[Optional[Any], Optional[List[str]]]:
    """
    Charge le DataFrame ML du run courant et la liste des colonnes features (90).
    Retourne (df_ml, feat_cols) ou (None, None) si indisponible.
    """
    if state is None:
        return None, None
    try:
        from src.services.ml_service import MLService, ML_NON_FEATURE_COLUMNS

        run_id = getattr(state, "run_id", "run_000")
        run_num = run_id.replace("run_", "")
        label_col = "score" if mode_ml == "Régression" else "classe"
        ml_svc = MLService()
        df_ml = ml_svc.preparer_run(run_num, label_column=label_col)
        if df_ml.empty:
            return None, None
        feat_cols = [c for c in df_ml.columns if c not in ML_NON_FEATURE_COLUMNS]
        return df_ml, feat_cols
    except Exception as e:
        logger.warning("_get_90_features_data: %s", e)
        return None, None


def _build_90_features_html_table(row_series: Any, feat_cols: List[str], arr: int, mois: int) -> str:
    """Construit un tableau HTML des 90 features (nom lisible → valeur), regroupé par bloc."""
    blocs: Dict[str, List[Tuple[str, str]]] = {
        "Central dernière semaine (sem_m1)": [],
        "Central semaine -2 (sem_m2)": [],
        "Central semaine -3 (sem_m3)": [],
        "Central semaine -4 (sem_m4)": [],
        "Voisins (moyenne) dernière semaine": [],
    }
    prefix_to_bloc = {
        "central_sem_m1_": "Central dernière semaine (sem_m1)",
        "central_sem_m2_": "Central semaine -2 (sem_m2)",
        "central_sem_m3_": "Central semaine -3 (sem_m3)",
        "central_sem_m4_": "Central semaine -4 (sem_m4)",
        "voisins_moy_sem_m1_": "Voisins (moyenne) dernière semaine",
    }
    for col in feat_cols:
        label = _feature_90_col_to_readable(col)
        val = row_series.get(col, "")
        for pre, bloc_name in prefix_to_bloc.items():
            if col.startswith(pre):
                blocs[bloc_name].append((label, str(val)))
                break
    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'/><style>",
        "body{font-family:Inter,sans-serif;padding:1rem;} table{border-collapse:collapse;width:100%;}",
        "th,td{border:1px solid #c9d6e3;padding:0.35rem 0.5rem;text-align:left;} th{background:#e8f4f8;}",
        "</style></head><body>",
        f"<h2>90 features ML — Arr. {arr} — Période (mois) {mois}</h2>",
    ]
    for bloc_name, pairs in blocs.items():
        if not pairs:
            continue
        parts.append(f"<h3>{bloc_name}</h3><table><thead><tr><th>Feature</th><th>Valeur</th></tr></thead><tbody>")
        for label, val in pairs:
            parts.append(f"<tr><td>{label}</td><td>{val}</td></tr>")
        parts.append("</tbody></table>")
    parts.append("</body></html>")
    return "".join(parts)


def _event_display_label(event: Any) -> str:
    """Libellé pour l'encart événements : type incident (Accident, Agression, Incendie) ou événement positif."""
    from src.core.events.event_grave import EventGrave
    from src.core.events.positive_event import PositiveEvent
    t = (getattr(event, "get_type", None) or (lambda: ""))()
    if isinstance(event, EventGrave):
        if t == "accident_grave":
            return "Accident"
        if t == "agression_grave":
            return "Agression"
        if t == "incendie_grave":
            return "Incendie"
        return t.replace("_", " ").title()
    if isinstance(event, PositiveEvent):
        labels = {"fin_travaux": "Fin travaux", "nouvelle_caserne": "Nouvelle caserne", "amelioration_materiel": "Amélioration matériel"}
        return labels.get(t, t.replace("_", " ").title())
    return str(t)


def _event_tooltip_text(event: Any) -> str:
    """Texte tooltip pour un événement (caractéristiques, casualties_base, duration, type)."""
    parts = []
    if hasattr(event, "characteristics") and event.characteristics:
        parts.append("Caractéristiques: " + ", ".join(f"{k}={v}" for k, v in event.characteristics.items()))
    if hasattr(event, "casualties_base"):
        parts.append(f"Morts de base: {event.casualties_base}")
    if hasattr(event, "duration"):
        parts.append(f"Durée: {event.duration} j")
    if hasattr(event, "arrondissement"):
        parts.append(f"Arrondissement: {event.arrondissement}")
    if hasattr(event, "impact_reduction"):
        parts.append(f"Réduction impact: {event.impact_reduction:.0%}")
    t = (getattr(event, "get_type", None) or (lambda: ""))()
    if t:
        parts.append(f"Type: {t}")
    return "\n".join(parts) if parts else "—"


def get_active_events_for_encart(state: Any, jour: int) -> List[Tuple[str, str, bool]]:
    """Retourne [(label, tooltip, is_grave), ...] pour les événements actifs (graves + positifs) au jour donné."""
    from src.core.events.event_grave import EventGrave
    result: List[Tuple[str, str, bool]] = []
    if state is None:
        return result
    for event in state.events_state.get_active_events_for_day(jour):
        label = _event_display_label(event)
        tooltip = _event_tooltip_text(event)
        result.append((label, tooltip, isinstance(event, EventGrave)))
    return result


def get_incidents_graves_vecteurs_for_encart(state: Any, jour: int) -> List[Tuple[str, str]]:
    """Incidents graves du jour issus des vecteurs (Vector.grave > 0) → [(label, tooltip), ...]."""
    result: List[Tuple[str, str]] = []
    if state is None:
        return result
    type_labels = {"accident": "Accident", "agression": "Agression", "incendie": "Incendie"}
    try:
        vs = state.vectors_state
        for mz_id in vs.get_all_microzones():
            vectors_mz = vs.get_vectors_for_day(mz_id, jour) or {}
            for inc_type, vec in vectors_mz.items():
                if vec and vec.grave > 0:
                    label = type_labels.get(inc_type, inc_type.title())
                    arr = microzone_to_arrondissement_mapped(mz_id)
                    tooltip = f"Incident grave · Type: {label} · Microzone: {mz_id} · Arrondissement: {arr}"
                    for _ in range(vec.grave):
                        result.append((label, tooltip))
    except Exception as e:
        logger.warning("get_incidents_graves_vecteurs_for_encart: %s", e)
    return result


# Clés pluriel (dynamic_state) → singulier (UI)
_PLURAL_TO_SINGULAR = {"accidents": "accident", "agressions": "agression", "incendies": "incendie"}


def _default_alcool_nuit() -> Dict[str, int]:
    """Valeurs par défaut pour alcool et nuit par type."""
    return {"accident": 0, "agression": 0, "incendie": 0}


def get_totaux_par_arrondissement(
    state: Any,
    jour: int,
    cumul_jours: bool = True,
) -> Dict[int, Dict[str, Any]]:
    """
    Totaux par arrondissement (1..20) et par type : accident, agression, incendie.
    Valeur par type = (total, benin, moyen, grave).
    Inclut aussi "alcool" et "nuit" : Dict[type, int] par type d'incident. Story 2.4.3.3.
    Si cumul_jours=True, additionne les statistiques du jour 0 au jour donné (cumul jour à jour).
    Mapping microzone → arrondissement : mêmes limites que features/casualties (limites_microzone_arrondissement.pkl).
    """
    out: Dict[int, Dict[str, Any]] = {
        arr: {
            "accident": (0, 0, 0, 0),
            "agression": (0, 0, 0, 0),
            "incendie": (0, 0, 0, 0),
            "alcool": _default_alcool_nuit(),
            "nuit": _default_alcool_nuit(),
        }
        for arr in range(1, 21)
    }
    if state is None:
        return out
    try:
        vs = state.vectors_state
        jours_a_sommer = range(0, jour + 1) if cumul_jours else [jour]
        for mz_id in vs.get_all_microzones():
            arr = microzone_to_arrondissement_mapped(mz_id)
            if arr not in out:
                out[arr] = {
                    "accident": (0, 0, 0, 0),
                    "agression": (0, 0, 0, 0),
                    "incendie": (0, 0, 0, 0),
                    "alcool": _default_alcool_nuit(),
                    "nuit": _default_alcool_nuit(),
                }
            for j in jours_a_sommer:
                vectors_mz = vs.get_vectors_for_day(mz_id, j) or {}
                for inc_type in ("accident", "agression", "incendie"):
                    vec = vectors_mz.get(inc_type)
                    if vec:
                        b, m, g = vec.benin, vec.moyen, vec.grave
                        total = b + m + g
                        prev = out[arr][inc_type]
                        out[arr][inc_type] = (
                            prev[0] + total, prev[1] + b, prev[2] + m, prev[3] + g,
                        )

        # Agrégation alcool et nuit depuis dynamic_state (clés pluriel) — état courant
        ds = getattr(state, "dynamic_state", None)
        if ds is not None:
            for mz_id in vs.get_all_microzones():
                arr = microzone_to_arrondissement_mapped(mz_id)
                alcool_mz = getattr(ds, "incidents_alcool", {}) or {}
                nuit_mz = getattr(ds, "incidents_nuit", {}) or {}
                for plural, singular in _PLURAL_TO_SINGULAR.items():
                    alc = alcool_mz.get(mz_id, {}).get(plural, 0)
                    nui = nuit_mz.get(mz_id, {}).get(plural, 0)
                    out[arr]["alcool"][singular] = out[arr]["alcool"].get(singular, 0) + alc
                    out[arr]["nuit"][singular] = out[arr]["nuit"].get(singular, 0) + nui
    except Exception as e:
        logger.warning("get_totaux_par_arrondissement: %s", e)
    return out


def _format_alcool_nuit_tooltip(alcool: Dict[str, int], nuit: Dict[str, int]) -> Tuple[str, str]:
    """Formate les lignes tooltip pour alcool et nuit avec totaux par type (émojis)."""
    emojis = {"accident": "🚗💥", "agression": "🔪", "incendie": "🔥"}
    parts_alcool = [f"{emojis[t]} {alcool.get(t, 0)}" for t in ("accident", "agression", "incendie")]
    parts_nuit = [f"{emojis[t]} {nuit.get(t, 0)}" for t in ("accident", "agression", "incendie")]
    alcool_str = ", ".join(parts_alcool) if any(alcool.values()) else "—"
    nuit_str = ", ".join(parts_nuit) if any(nuit.values()) else "—"
    return f"🌙 (nuit) : {nuit_str}", f"🍷 (alcool) : {alcool_str}"


def _render_central_row_and_jours(
    ph_events: Any,
    ph_map: Any,
    ph_arr: Any,
    ph_jours: Any,
    state: Optional[Any],
    jour_actuel: int,
    total: int,
    run_actuel: int,
    ml_training_pct: float,
    microzones: Optional[gpd.GeoDataFrame],
    map_center: Tuple[float, float],
    map_zoom: int,
) -> None:
    """Remplit les placeholders (événements, carte, arrondissements, Jours X/Y) sans rerun de la page."""
    with ph_events.container():
        st.caption("Événements")
        active_events = get_active_events_for_encart(state, jour_actuel) if state else []
        incidents_graves = get_incidents_graves_vecteurs_for_encart(state, jour_actuel) if state else []
        events_html = build_events_column_html(active_events, incidents_graves)
        st.components.v1.html(
            '<div style="width:100%;min-height:200px;">' + events_html + "</div>",
            height=min(400, 200 + (len(active_events) + len(incidents_graves)) * 32),
            scrolling=False,
        )

    with ph_map.container():
        if microzones is not None and len(microzones) > 0:
            nb_mz = len(microzones)
            st.caption(f"🗺️ Carte Paris — {nb_mz} microzone{'s' if nb_mz > 1 else ''} affichée{'s' if nb_mz > 1 else ''}")
            map_events = build_map_events_from_state(state, jour_actuel) if state else []
            show_casernes_hopitaux = st.session_state.get("show_casernes_hopitaux", False)
            df_locations = load_locations_casernes_hopitaux() if show_casernes_hopitaux else None
            m = build_map_paris(
                microzones,
                events=map_events if map_events else None,
                state=state,
                jour=jour_actuel,
                location=map_center,
                zoom_start=map_zoom,
                show_casernes_hopitaux=show_casernes_hopitaux,
                df_locations=df_locations,
            )
            map_html = wrap_map_html(m._repr_html_())
            st.components.v1.html(map_html, height=CARTE_IFRAME_HEIGHT, scrolling=False)
        else:
            st.caption("🗺️ Carte Paris — microzones")
            st.warning("Données microzones absentes.")
            st.components.v1.html(
                '<div style="width:100%; height:100%; background:#f0f0f0; display:flex; align-items:center; justify-content:center;">Carte non disponible</div>',
                height=CARTE_IFRAME_HEIGHT,
                scrolling=False,
            )

    with ph_arr.container():
        st.caption("20 arrondissements (cumul J0→J" + str(jour_actuel) + ")")
        totaux = get_totaux_par_arrondissement(state, jour_actuel) if state else {}
        if not totaux:
            totaux = {
                arr: {
                    "accident": (0, 0, 0, 0),
                    "agression": (0, 0, 0, 0),
                    "incendie": (0, 0, 0, 0),
                    "alcool": _default_alcool_nuit(),
                    "nuit": _default_alcool_nuit(),
                }
                for arr in range(1, 21)
            }
        arr_html = build_arrondissements_column_html(totaux, jour_actuel)
        st.components.v1.html(
            '<div style="width:100%;">' + arr_html + "</div>",
            height=min(680, 80 + 20 * 32),
            scrolling=False,
        )

    with ph_jours.container():
        st.markdown(f"<small><b>Jours</b> {jour_actuel}/{total}</small>", unsafe_allow_html=True)


def _render_prediction_cols(
    ph_col_pred: Any,
    ph_col_label: Any,
    state: Any,
    jour_actuel: int,
    mode_ml: str,
    microzones: Any,
) -> None:
    """
    Colonne 2 : uniquement les prédictions (période à venir, sem. 4→8, 8→12, etc.)
    Colonne 3 : uniquement les labels réels (période passée, sem. 0→4, 4→8, etc.)
    L'écart/verdict en col 3 compare réel vs prédiction pour LA MÊME période.
    """
    labels_pp = st.session_state.get("ml_labels_par_periode", {})
    preds_pp = st.session_state.get("ml_preds_par_periode", {})
    periode_pred, periode_label = _get_periode_pred_label(jour_actuel)

    # Colonne 2 : PRÉDICTIONS — pendant JOURS_RETENTION_PRED après une fin de période,
    # garder la prédiction de la période qui vient de finir (pour comparer avec col 3).
    # Sinon, afficher la prédiction de la période à venir.
    jours_depuis_fin_periode = jour_actuel % JOURS_PAR_PERIODE if jour_actuel >= JOURS_PAR_PERIODE else 999
    en_retention = jours_depuis_fin_periode < JOURS_RETENTION_PRED
    mois_col2 = periode_label if (periode_label and en_retention) else (periode_label or 0) + 1
    preds_col2 = preds_pp.get(mois_col2, {}) if periode_label else {}

    # Colonne 3 : LABELS RÉELS — labels pour la période qui vient de se terminer (periode_label)
    # À J28 : réel J0-J28 ; à J56 : réel J28-J56 ; etc.
    labels_col3 = labels_pp.get(periode_label, {}) if periode_label else {}

    # Pour l'écart/verdict en col 3 : prédiction pour LA MÊME période que le label
    preds_pour_verdict = preds_pp.get(periode_label, {}) if periode_label else {}

    col2_active = len(preds_col2) > 0
    col3_active = len(labels_col3) > 0
    is_regression = mode_ml == "Régression"

    # --- Colonne 2 : affichage des PRÉDICTIONS uniquement ---
    html_pred = '<div style="width:100%;">'
    for arr in range(1, 21):
        val = preds_col2.get(arr, "—")
        try:
            vf = float(val)
        except (TypeError, ValueError):
            vf = 2 if "normal" in str(val or "").lower() else (5 if "pre" in str(val or "").lower() else (8 if "cata" in str(val or "").lower() else None))
        border = f"3px solid {_value_to_gradient_rgb(vf)}" if (vf is not None and col2_active) else "1px solid #c9d6e3"
        html_pred += f'<div class="pastel-box" style="min-height:1.8rem;border:{border};"><span class="pastel-box-roman">{val}</span></div>'
    html_pred += "</div>"
    with ph_col_pred.container():
        j_deb = (mois_col2 - 1) * JOURS_PAR_PERIODE
        j_fin = mois_col2 * JOURS_PAR_PERIODE
        suffix = " [comparaison]" if en_retention else ""
        st.caption(f"Prédiction (J{j_deb}→J{j_fin}){suffix}")
        st.markdown(html_pred, unsafe_allow_html=True)

    # --- Colonne 3 : affichage des LABELS RÉELS uniquement, avec écart/verdict vs prédiction même période ---
    html_label = '<div style="width:100%;">'
    for arr in range(1, 21):
        val = labels_col3.get(arr, "—")
        pred_val_verdict = preds_pour_verdict.get(arr)
        try:
            vf = float(val)
            pred_f = float(pred_val_verdict) if pred_val_verdict is not None else None
        except (TypeError, ValueError):
            vf = 2 if "normal" in str(val or "").lower() else (5 if "pre" in str(val or "").lower() else (8 if "cata" in str(val or "").lower() else None))
            pred_f = None
        border = f"3px solid {_value_to_gradient_rgb(vf)}" if (vf is not None and col3_active) else "1px solid #c9d6e3"
        inner = f'<span class="pastel-box-roman">{val}</span>'
        if is_regression and pred_f is not None and col3_active:
            ecart = vf - pred_f
            ecart_color = _ecart_to_color_regression(ecart)
            tx = 30 * (1 if (arr % 2) else -1)
            ty = -40 - (arr % 3) * 15
            inner += f'<span class="fly-ecart" style="color:{ecart_color};position:absolute;top:-0.2rem;left:50%;--fx:translate({tx}px,{ty}px);">{ecart:+.1f}</span>'
        elif not is_regression and val != "—" and col3_active:
            verdict, vcolor = _category_verdict(str(pred_val_verdict or ""), str(val))
            if verdict != "—":
                inner += f'<br/><span style="font-size:0.65rem;color:{vcolor};font-weight:600;">{verdict}</span>'
        html_label += f'<div class="pastel-box" style="min-height:1.8rem;border:{border};position:relative;">{inner}</div>'
    html_label += "</div>"
    with ph_col_label.container():
        j_deb_l = (periode_label - 1) * JOURS_PAR_PERIODE if periode_label else 0
        j_fin_l = periode_label * JOURS_PAR_PERIODE if periode_label else JOURS_PAR_PERIODE
        st.caption(f"Label réel (J{j_deb_l}→J{j_fin_l})")
        st.markdown(html_label, unsafe_allow_html=True)


def list_ml_models() -> Tuple[List[str], List[str]]:
    """Retourne (modèles régression, modèles classification) depuis data/models."""
    root = PathResolver.get_project_root()
    reg_dir = root / "data" / "models" / "regression"
    clf_dir = root / "data" / "models" / "classification"
    reg = sorted([f.stem for f in reg_dir.glob("*.joblib")]) if reg_dir.exists() else []
    clf = sorted([f.stem for f in clf_dir.glob("*.joblib")]) if clf_dir.exists() else []
    if not reg:
        reg = ["ridge_001_default", "huber_regressor_001_default"]
    if not clf:
        clf = ["logistic_regression_001_default"]
    return reg, clf


def _get_next_model_number() -> str:
    """Génère le prochain numéro d'entraînement (001, 002, ...)."""
    reg, clf = list_ml_models()
    all_nums = []
    for name in reg + clf:
        parts = name.split("_")
        if len(parts) >= 2 and parts[1].isdigit():
            all_nums.append(int(parts[1]))
    next_num = max(all_nums, default=0) + 1
    return f"{next_num:03d}"


def _run_ml_training(
    mode_ml: str,
    algo_choisi: str,
    nom_modele: str,
    compute_shap: bool,
    scenario: str,
    variabilite: str,
    nb_jours: int,
    nb_runs: int = 50,
    progress_callbacks: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Lance l'entraînement ML : N runs headless, extraction, entraînement.
    Utilise nb_jours (identique au run affiché) et nb_runs (sélection utilisateur).
    """
    from src.services.ml_service import MLService, MLTrainer, compute_shap_values, HAS_SHAP

    result: Dict[str, Any] = {"ok": False, "metrics": {}, "path": None, "error": None}
    cbs = progress_callbacks or {}

    try:
        config_path = str(PathResolver.get_project_root() / "config" / "config.yaml")
        config = load_and_validate_config(config_path)
        sim_svc = SimulationService(config=config)

        # N runs headless (même nb_jours que le run affiché)
        for run_idx in range(nb_runs):
            sim_svc.run_single_headless_run(
                run_idx=run_idx,
                days=nb_jours,
                save_pickles=True,
                save_trace=True,
                scenario_ui=scenario,
                variabilite_ui=variabilite,
                verbose=False,
            )
            if "on_run_done" in cbs:
                cbs["on_run_done"](run_idx + 1, nb_runs)

        def _table_progress(cur: int, tot: int, phase: str) -> None:
            if "on_table_progress" in cbs:
                cbs["on_table_progress"](int(100 * cur / tot) if tot > 0 else 0)

        ml_svc = MLService()
        label_col = "score" if mode_ml == "Régression" else "classe"
        df_ml = ml_svc.workflow_extract_then_prepare(
            nb_runs=nb_runs,
            label_column=label_col,
            verbose=False,
            calibrate_classification=(mode_ml == "Classification"),
            progress_callback=_table_progress,
        )

        if df_ml.empty or len(df_ml) < 10:
            result["error"] = "Données ML insuffisantes (min 10 lignes)"
            return result

        numero = _get_next_model_number()
        trainer = MLTrainer()

        if mode_ml == "Régression":
            res = trainer.train_regression_models(
                df_ml, label_column="score", numero_entrainement=numero, params_str=nom_modele or "default"
            )
            algo_map = {"Ridge": "ridge", "Huber": "huber_regressor"}
            key = algo_map.get(algo_choisi, "ridge")
            if key in res:
                result["metrics"] = res[key]["metrics"]
                result["path"] = str(res[key]["path"])
        else:
            res = trainer.train_classification_models(
                df_ml, label_column="classe", numero_entrainement=numero, params_str=nom_modele or "default"
            )
            algo_map = {"Logistic Regression": "logistic_regression", "Gradient Boosting": "xgboost"}
            key = algo_map.get(algo_choisi, "logistic_regression")
            if key in res and res[key]:
                result["metrics"] = res[key]["metrics"]
                result["path"] = str(res[key]["path"])

        if result["path"] and compute_shap and HAS_SHAP:
            try:
                from src.services.ml_service import _get_ml_feature_columns, ML_NON_FEATURE_COLUMNS
                payload = MLTrainer.load_model(result["path"])
                feat_cols = payload.get("metadata", {}).get("feature_columns", [])
                X = df_ml[[c for c in feat_cols if c in df_ml.columns]].head(50)
                if len(X) > 0:
                    model = payload["model"]
                    model_type = "tree" if "xgboost" in str(type(model)).lower() else "linear"
                    shap_res = compute_shap_values(model, X, feature_names=feat_cols, model_type=model_type, max_samples=30)
                    result["shap"] = shap_res
            except Exception as e:
                result["shap_error"] = str(e)

        if "on_training_done" in cbs:
            cbs["on_training_done"](100)
        result["ok"] = True
    except Exception as e:
        result["error"] = str(e)
        logger.exception("Erreur entraînement ML: %s", e)

    return result


def _launch_ml_training_after_visible_run(
    ph_run: Optional[Any] = None,
    ph_table_ml: Optional[Any] = None,
    ph_ml_training: Optional[Any] = None,
) -> None:
    """
    Lance l'entraînement ML après la fin du run visible (mode Entraînement).
    N runs headless (même nb_jours que run affiché) + extraction + entraînement.
    Met à jour les placeholders Run, Table ML, ML training pendant l'exécution.
    """
    import streamlit as st

    # Récupérer paramètres de la session (total_jours et nb_runs verrouillés à LANCEMENT)
    mode_ml = st.session_state.get("mode_ml", "Régression")
    algo_choisi = st.session_state.get("algo_choisi", "Ridge")
    nom_modele = st.session_state.get("nom_modele_ml", "default")
    compute_shap = st.session_state.get("compute_shap", False)
    scenario = st.session_state.get("scenario_ui", "Scénario Normal")
    variabilite = st.session_state.get("variabilite_ui", "Normale")
    nb_jours = st.session_state.get("total_jours", 392)
    nb_runs = st.session_state.get("nb_runs", 50)

    def on_run_done(current: int, total: int) -> None:
        st.session_state["run_actuel"] = current
        if ph_run is not None:
            ph_run.markdown(f"<small><b>Run</b> {current}/{total}</small>", unsafe_allow_html=True)

    def on_table_progress(pct: int) -> None:
        st.session_state["ml_table_pct"] = pct
        if ph_table_ml is not None:
            ph_table_ml.markdown(f"<small><b>Table ML</b> {pct}%</small>", unsafe_allow_html=True)

    def on_training_done(pct: int) -> None:
        st.session_state["ml_training_pct"] = pct
        if ph_ml_training is not None:
            ph_ml_training.markdown(f"<small><b>ML training</b> {pct}%</small>", unsafe_allow_html=True)

    progress_callbacks = {
        "on_run_done": on_run_done,
        "on_table_progress": on_table_progress,
        "on_training_done": on_training_done,
    }

    # Pas de spinner pour permettre la mise à jour des placeholders
    res = _run_ml_training(
        mode_ml=mode_ml,
        algo_choisi=algo_choisi,
        nom_modele=nom_modele or "default",
        compute_shap=compute_shap,
        scenario=scenario,
        variabilite=variabilite,
        nb_jours=nb_jours,
        nb_runs=nb_runs,
        progress_callbacks=progress_callbacks,
    )

    if res.get("ok"):
        model_path = res.get("path", "")
        st.session_state["last_trained_model_path"] = model_path
        st.session_state["last_trained_metrics"] = res.get("metrics", {})
        st.session_state["last_trained_mode"] = mode_ml
        st.session_state["last_trained_shap"] = res.get("shap")
        st.session_state["show_save_dialog"] = True
        st.rerun()
    else:
        st.error(f"Erreur entraînement ML: {res.get('error', 'Erreur inconnue')}")


JOURS_PAR_PERIODE = 28  # 4 semaines
JOURS_RETENTION_PRED = 10  # garder la prédiction N jours après fin de période pour comparer


def _value_to_gradient_rgb(val: float, vmin: float = 0, vmid: float = 5, vmax: float = 10) -> str:
    """Couleur dégradé : vert foncé (0) → bleu clair (5) → rouge foncé (10)."""
    val = max(vmin, min(vmax, val))
    if val <= vmid:
        t = (val - vmin) / (vmid - vmin) if vmid > vmin else 0
        # vert foncé #0d5c0d → bleu clair #5dade2
        r = int(13 + (90 - 13) * t)
        g = int(92 + (173 - 92) * t)
        b = int(13 + (226 - 13) * t)
    else:
        t = (val - vmid) / (vmax - vmid) if vmax > vmid else 0
        # bleu clair #5dade2 → rouge foncé #922b21
        r = int(93 + (146 - 93) * t)
        g = int(173 + (43 - 173) * t)
        b = int(226 + (33 - 226) * t)
    return f"rgb({r},{g},{b})"


def _ecart_to_color_regression(ecart: float) -> str:
    """Vert si <0.5, dégradé vers rouge si >3."""
    abs_e = abs(ecart)
    if abs_e <= 0.5:
        return "#0d5c0d"
    if abs_e >= 3:
        return "#922b21"
    t = (abs_e - 0.5) / 2.5
    r = int(13 + (146 - 13) * t)
    g = int(92 + (43 - 92) * t)
    b = int(13 + (33 - 13) * t)
    return f"rgb({r},{g},{b})"


def _category_verdict(pred: str, label: str) -> Tuple[str, str]:
    """Retourne (texte, couleur): correct/incorrect/faux + vert/orange/rouge."""
    ORDER = ["Normal", "Pre-catastrophique", "Catastrophique"]
    def idx(s: str) -> int:
        for i, c in enumerate(ORDER):
            if c.lower() in (s or "").lower():
                return i
        return -1
    i_pred, i_label = idx(pred), idx(label)
    if i_pred < 0 or i_label < 0:
        return ("—", "#666")
    diff = abs(i_pred - i_label)
    if diff == 0:
        return ("correct", "#0d5c0d")
    if diff == 1:
        return ("incorrect", "#e67e22")
    return ("faux", "#922b21")


def _export_features_labels_csv() -> Tuple[Optional[str], Optional[str]]:
    """
    Exporte les features et labels du dernier run en CSV.
    Story 2.4.5 : Export CSV (features, labels).

    Returns:
        (features_path, labels_path) ou (None, None) si erreur
    """
    from datetime import datetime
    try:
        from src.services.ml_service import MLService
        import streamlit as st
        nb_runs_export = st.session_state.get("nb_runs_sel", 50)
        ml_svc = MLService()
        df_ml = ml_svc.workflow_50_runs(nb_runs=nb_runs_export, verbose=False)
        if df_ml.empty:
            return None, None

        export_dir = PathResolver.get_project_root() / "data" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        features_path = export_dir / f"features_{ts}.csv"
        labels_path = export_dir / f"labels_{ts}.csv"

        # Colonnes features (exclure meta et label)
        meta_cols = ["run_id", "arrondissement", "mois", "label", "score", "classe"]
        feat_cols = [c for c in df_ml.columns if c not in meta_cols]

        df_features = df_ml[["run_id", "arrondissement", "mois"] + feat_cols]
        df_labels = df_ml[["run_id", "arrondissement", "mois"] + [c for c in ["score", "classe", "label"] if c in df_ml.columns]]

        df_features.to_csv(features_path, index=False)
        df_labels.to_csv(labels_path, index=False)

        logger.info("Export CSV : %s, %s", features_path, labels_path)
        return str(features_path), str(labels_path)
    except Exception as e:
        logger.exception("Erreur export CSV: %s", e)
        return None, None


def _export_map_html(state: Any, jour: int) -> Optional[str]:
    """
    Exporte la carte Folium en HTML.
    Story 2.4.5 : Export HTML (cartes).

    Returns:
        Chemin du fichier HTML ou None si erreur
    """
    from datetime import datetime
    try:
        microzones = load_microzones()
        if microzones is None:
            return None

        map_events = build_map_events_from_state(state, jour) if state else []
        show_ch = st.session_state.get("show_casernes_hopitaux", False)
        df_loc = load_locations_casernes_hopitaux() if show_ch else None
        m = build_map_paris(
            microzones,
            events=map_events,
            state=state,
            jour=jour,
            show_casernes_hopitaux=show_ch,
            df_locations=df_loc,
        )

        export_dir = PathResolver.get_project_root() / "data" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = export_dir / f"carte_{ts}.html"
        m.save(str(html_path))

        logger.info("Export carte HTML : %s", html_path)
        return str(html_path)
    except Exception as e:
        logger.exception("Erreur export carte: %s", e)
        return None


def _save_emergency_state(state: Any) -> Optional[str]:
    """
    Sauvegarde l'état d'urgence (safe state) lors de l'arrêt.
    Story 2.4.5 : Sauvegarde automatique lors [Stop].

    Returns:
        Chemin du fichier pickle ou None si erreur
    """
    from datetime import datetime
    try:
        safe_dir = PathResolver.get_project_root() / "data" / "safe_state"
        safe_dir.mkdir(parents=True, exist_ok=True)

        run_id = getattr(state, "run_id", "run_unknown")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_path = safe_dir / f"{run_id}_safe_{ts}.pkl"

        state.save(str(safe_path))
        logger.info("État d'urgence sauvegardé : %s", safe_path)
        return str(safe_path)
    except Exception as e:
        logger.exception("Erreur sauvegarde état d'urgence: %s", e)
        return None


def _load_emergency_state(safe_path: str) -> Optional[Any]:
    """
    Charge un état d'urgence depuis un fichier pickle.
    Story 2.4.5 : Reprise après interruption.

    Returns:
        SimulationState ou None si erreur
    """
    try:
        from src.core.state.simulation_state import SimulationState
        state = SimulationState.load(safe_path)
        logger.info("État d'urgence chargé : %s", safe_path)
        return state
    except Exception as e:
        logger.exception("Erreur chargement état d'urgence: %s", e)
        return None


def _list_safe_states() -> List[str]:
    """
    Liste les fichiers d'état d'urgence disponibles.
    Story 2.4.5 : Reprise après interruption.

    Returns:
        Liste des chemins de fichiers pickle
    """
    safe_dir = PathResolver.get_project_root() / "data" / "safe_state"
    if not safe_dir.exists():
        return []
    return sorted([str(f) for f in safe_dir.glob("*.pkl")], reverse=True)


def _get_periode_pred_label(jour_actuel: int) -> Tuple[Optional[int], Optional[int]]:
    """
    Détermine quelle période afficher pour col 2 (prédiction) et col 3 (label).

    Col 2 : prédiction pour la période à venir (J28→J56, J56→J84, etc.)
            Affichée dès J28 (quand on a les données pour la calculer) et conservée jusqu'à la fin de la période.
    Col 3 : label réel de la période qui vient de se terminer (J0→J28, J28→J56, etc.)
            Affiché dès J28, J56, J84...

    période_label = numéro de période terminée (1=J0-28, 2=J28-56, ...), None si < J28
    période_pred = période_label (même base : pred pour période_label+1)
    """
    if jour_actuel < JOURS_PAR_PERIODE:
        return None, None
    periode_label = jour_actuel // JOURS_PAR_PERIODE
    if periode_label < 1:
        return None, None
    return periode_label, periode_label


def _run_ml_prediction_full(
    mode_ml: str,
    modele_choisi: str,
    state: Any,
) -> Tuple[Optional[Dict[int, Dict[int, Any]]], Optional[Dict[int, Dict[int, Any]]], Optional[str]]:
    """
    Lance prédictions et labels pour toutes les périodes.
    Retourne (labels_par_periode, predictions_par_periode, error).
    labels_par_periode[periode][arr] = valeur réelle
    predictions_par_periode[periode][arr] = prédiction (calculée avec features période-1)
    """
    import numpy as np
    from src.services.ml_service import MLService, MLTrainer
    from src.services.ml_data_extractor import extract_and_save_ml_data

    if state is None:
        return None, None, "Aucun état de simulation"

    try:
        run_id = getattr(state, "run_id", "run_000")
        run_num = run_id.replace("run_", "")

        if not extract_and_save_ml_data(state=state, run_id=run_num, prediction_min=True):
            return None, None, "Impossible d'extraire features/labels"

        label_col = "score" if mode_ml == "Régression" else "classe"
        ml_svc = MLService()
        df_ml = ml_svc.preparer_run(run_num, label_column=label_col)
        if df_ml.empty:
            return None, None, "DataFrame ML vide"

        root = PathResolver.get_project_root()
        subdir = "regression" if mode_ml == "Régression" else "classification"
        model_path = root / "data" / "models" / subdir / f"{modele_choisi}.joblib"
        if not model_path.exists():
            return None, None, f"Modèle introuvable: {model_path}"

        payload = MLTrainer.load_model(model_path)

        labels_par_periode: Dict[int, Dict[int, Any]] = {}
        preds_par_periode: Dict[int, Dict[int, Any]] = {}

        for idx, row in df_ml.iterrows():
            arr = int(row["arrondissement"])
            mois = int(row["mois"])
            if mois not in labels_par_periode:
                labels_par_periode[mois] = {}
                preds_par_periode[mois] = {}
            labels_par_periode[mois][arr] = row["label"]

            X_row = MLTrainer._prepare_X_for_prediction(
                df_ml.loc[[idx]], payload, df_ml=df_ml
            )
            if X_row is None or len(X_row) == 0:
                continue
            if mode_ml == "Régression":
                p = MLTrainer.predict_regression(payload, X_row)[0]
                preds_par_periode[mois][arr] = float(p)
            else:
                p = MLTrainer.predict_classification(payload, X_row)[0]
                model = payload.get("model")
                if hasattr(model, "classes_"):
                    classes_ = model.classes_
                    preds_par_periode[mois][arr] = str(classes_[int(p)]) if 0 <= int(p) < len(classes_) else str(p)
                else:
                    preds_par_periode[mois][arr] = str(p)

        # Prédiction période K+1 = modèle(features période K) — pour affichage 18j avant fin K+1
        for mois in sorted(labels_par_periode.keys()):
            mois_suivant = mois + 1
            if mois_suivant not in preds_par_periode:
                preds_par_periode[mois_suivant] = {}
            for arr in labels_par_periode[mois]:
                row = df_ml[(df_ml["arrondissement"] == arr) & (df_ml["mois"] == mois)]
                if row.empty:
                    continue
                X_row = MLTrainer._prepare_X_for_prediction(row, payload, df_ml=df_ml)
                if X_row is None or len(X_row) == 0:
                    continue
                if mode_ml == "Régression":
                    p = MLTrainer.predict_regression(payload, X_row)[0]
                    preds_par_periode[mois_suivant][arr] = float(p)
                else:
                    p = MLTrainer.predict_classification(payload, X_row)[0]
                    model = payload.get("model")
                    if hasattr(model, "classes_"):
                        classes_ = model.classes_
                        preds_par_periode[mois_suivant][arr] = str(classes_[int(p)]) if 0 <= int(p) < len(classes_) else str(p)
                    else:
                        preds_par_periode[mois_suivant][arr] = str(p)

        return labels_par_periode, preds_par_periode, None
    except Exception as e:
        logger.exception("Erreur prédiction ML: %s", e)
        return None, None, str(e)


def _run_ml_prediction(
    mode_ml: str,
    modele_choisi: str,
    state: Any,
) -> Tuple[Optional[Dict[int, Any]], Optional[Dict[int, Any]], Optional[str]]:
    """Wrapper pour compatibilité : retourne (labels_arr, preds_arr) du dernier mois."""
    labels_pp, preds_pp, err = _run_ml_prediction_full(mode_ml, modele_choisi, state)
    if err:
        return None, None, err
    if not labels_pp or not preds_pp:
        return None, None, None
    last_mois = max(labels_pp.keys()) if labels_pp else 1
    return labels_pp.get(last_mois, {}), preds_pp.get(last_mois, {}), None


def main() -> None:
    # --- Enregistrer position et zoom carte depuis l'URL (mis à jour par le script dans l'iframe à chaque pan/zoom) ---
    try:
        q = st.query_params
        lat_s = q.get("map_lat")
        lng_s = q.get("map_lng")
        zoom_s = q.get("map_zoom")
        if lat_s is not None and lng_s is not None and zoom_s is not None:
            lat_f = float(lat_s)
            lng_f = float(lng_s)
            zoom_i = int(zoom_s)
            if -90 <= lat_f <= 90 and -180 <= lng_f <= 180 and 1 <= zoom_i <= 20:
                st.session_state["map_center"] = (lat_f, lng_f)
                st.session_state["map_zoom"] = zoom_i
    except (ValueError, TypeError, AttributeError):
        pass

    # --- Ligne très fine dédiée au titre, pleine largeur (au-dessus de tout le reste) ---
    st.markdown("### 🚒 Simulation Risques Paris")

    # --- Bandeau contrôles ---
    # Nb jours et Nb runs DOIVENT être rendus AVANT le bouton LANCEMENT pour que leurs valeurs soient lues au clic
    from src.services.ml_data_extractor import get_allowed_durations_days
    allowed_days_top = get_allowed_durations_days()
    _nb_jours_def = st.session_state.get("nb_jours", st.session_state.get("total_jours", 392))
    _nb_jours_idx_top = allowed_days_top.index(_nb_jours_def) if _nb_jours_def in allowed_days_top else 5
    _nb_runs_opts_top = [5, 10, 20, 50, 100, 250]
    _nb_runs_def = st.session_state.get("nb_runs", st.session_state.get("nb_runs_sel", 50))
    _nb_runs_idx_top = _nb_runs_opts_top.index(_nb_runs_def) if _nb_runs_def in _nb_runs_opts_top else 3

    # Scénario | Variabilité | Nb jours | Nb runs | LANCEMENT | (spacer) | Radio | Type modèle | Modèle+Algo
    (
        col_scenario,
        col_variabilite,
        col_nb_jours,
        col_nb_runs,
        col_lancer,
        col_spacer,
        col_radio,
        col_type,
        col_mod_algo,
    ) = st.columns([3, 3, 3, 2, 4, 3, 5, 5, 6])

    with col_scenario:
        scenario = st.selectbox("Scénario", ["Standard", "Optimiste", "Pessimiste"], key="scenario")
    with col_variabilite:
        variabilite = st.selectbox("Variabilité", ["Faible", "Moyenne", "Forte"], key="variabilite")
    with col_nb_jours:
        nb_jours_bandeau = st.selectbox(
            "Nb jours",
            options=allowed_days_top,
            index=_nb_jours_idx_top,
            format_func=lambda x: f"{x} j",
            key="nb_jours",
            label_visibility="visible",
        )
    with col_nb_runs:
        nb_runs_bandeau = st.selectbox(
            "Nb runs",
            options=_nb_runs_opts_top,
            index=_nb_runs_idx_top,
            format_func=lambda x: str(x),
            key="nb_runs_sel",
            label_visibility="visible",
        )

    # Bouton LANCEMENT / PAUSE / REPRENDRE : état déduit de la session
    _jour = st.session_state.get("jour_actuel", 0)
    _total = st.session_state.get("total_jours", 365)
    _lancee = st.session_state.get("simulation_lancee", False)
    _has_state = st.session_state.get("simulation_state") is not None
    _en_cours = _has_state and 0 <= _jour < _total
    if _lancee:
        btn_label = "PAUSE"
    elif _en_cours:
        btn_label = "REPRENDRE"
    else:
        btn_label = "LANCEMENT"
    with col_lancer:
        btn_clicked = st.button(btn_label, type="primary", key="btn_lancer_pause_reprendre")

    if btn_clicked:
        if btn_label == "PAUSE":
            # Figer l'écran et arrêter l'avancement backend + sauvegarde état d'urgence (Story 2.4.5)
            st.session_state["simulation_lancee"] = False
            _state = st.session_state.get("simulation_state")
            if _state:
                safe_path = _save_emergency_state(_state)
                st.session_state["last_safe_state_path"] = safe_path
                logger.info("Simulation en pause — état d'urgence sauvegardé: %s", safe_path)
                try:
                    st.toast(f"Simulation en pause. État sauvegardé: {safe_path}")
                except Exception:
                    pass
            else:
                logger.info("Simulation en pause — aucun état à sauvegarder.")
                try:
                    st.toast("Simulation en pause.")
                except Exception:
                    pass
            st.rerun()
        elif btn_label == "REPRENDRE":
            # Relancer l'avancement jour par jour (backend + affichage)
            st.session_state["simulation_lancee"] = True
            logger.info("Simulation reprise — avancement jour par jour.")
            try:
                st.toast("Simulation reprise.")
            except Exception:
                pass
            st.rerun()
        else:
            # LANCEMENT : utiliser nb_jours et nb_runs du bandeau (déjà rendus au-dessus)
            _total_jours = nb_jours_bandeau if nb_jours_bandeau in allowed_days_top else min(allowed_days_top, key=lambda x: abs(x - nb_jours_bandeau))
            _nb_runs = nb_runs_bandeau if nb_runs_bandeau in _nb_runs_opts_top else 50

            launch_seed = random.randint(0, 2**31 - 1)
            _mode_radio_launch = st.session_state.get("mode_radio", "Entraînement")
            st.session_state["jour_actuel"] = 0
            st.session_state["liste_morts"] = []
            st.session_state["liste_blesses_graves"] = []
            st.session_state["total_jours"] = _total_jours
            st.session_state["nb_runs"] = _nb_runs
            st.session_state["run_actuel"] = 1
            st.session_state["simulation_lancee"] = True
            st.session_state["scenario_ui"] = scenario
            st.session_state["variabilite_ui"] = variabilite
            st.session_state["run_seed"] = launch_seed
            st.session_state["launch_mode_radio"] = _mode_radio_launch
            st.session_state["ml_training_pending"] = (_mode_radio_launch == "Entraînement")
            total = _total_jours
            try:
                config_path = str(PathResolver.get_project_root() / "config" / "config.yaml")
                config = load_and_validate_config(config_path)
                sim = SimulationService(config=config, seed=launch_seed)
                state = sim.run_one(days=1, scenario_ui=scenario, variabilite_ui=variabilite)
                st.session_state["simulation_state"] = state
                print(f"[Streamlit] Simulation lancée — Run 1/{_nb_runs}, seed={launch_seed}, Jours 0/{total} (avancement jour par jour, 0,33 s/jour)")
                logger.info("Simulation lancée — Run 1, seed=%s, avancement des jours (0,33 s/jour)", launch_seed)
                st.toast(f"Simulation lancée — Run 1, seed {launch_seed}, Jours 0 → avancement jour par jour.")
            except Exception as e:
                logger.exception("Lancement simulation: %s", e)
                st.session_state["simulation_state"] = None
                try:
                    st.toast(f"Erreur lancement simulation: {e}")
                except Exception:
                    pass
            st.rerun()

    # --- Bouton Charger état sauvegardé (Story 2.4.5) — uniquement en mode Entraînement ---
    safe_states = _list_safe_states()
    if safe_states and not _lancee and st.session_state.get("mode_radio", "Entraînement") != "Prédiction":
        with st.expander("📂 Charger un état sauvegardé", expanded=False):
            safe_file = st.selectbox(
                "État disponible",
                options=safe_states,
                format_func=lambda x: Path(x).name,
                key="select_safe_state",
            )
            if st.button("Charger cet état", key="btn_load_safe"):
                loaded = _load_emergency_state(safe_file)
                if loaded:
                    st.session_state["simulation_state"] = loaded
                    st.session_state["jour_actuel"] = loaded.current_day
                    st.session_state["run_actuel"] = 1
                    st.session_state["simulation_lancee"] = False
                    st.session_state["liste_morts"] = []
                    st.session_state["liste_blesses_graves"] = []
                    st.success(f"État chargé : jour {loaded.current_day}")
                    st.rerun()
                else:
                    st.error("Erreur lors du chargement")

    with col_radio:
        _mode = st.session_state.get("mode_radio", "Entraînement")
        _pred = st.button("○ Prédiction" if _mode != "Prédiction" else "● Prédiction", key="btn_mode_pred")
        if _pred:
            st.session_state["mode_radio"] = "Prédiction"
            st.rerun()
        st.markdown('<div class="radio-options-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
        _ent = st.button("○ Entraînement" if _mode != "Entraînement" else "● Entraînement", key="btn_mode_ent")
        if _ent:
            st.session_state["mode_radio"] = "Entraînement"
            st.rerun()
        mode_radio = st.session_state.get("mode_radio", "Entraînement")
    with col_type:
        st.markdown(
            f'<div class="type-modele-spacer" style="height:{TYPE_MODELE_SPACER_REM}rem;margin:0;padding:0;line-height:0;font-size:0;" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        mode_ml = st.selectbox("Type de modèle", ["Régression", "Classification"], key="mode_ml")
    with col_mod_algo:
        reg_models, clf_models = list_ml_models()
        modeles_dispo = clf_models if mode_ml == "Classification" else reg_models
        modele_choisi = st.selectbox(
            "Modèle entrainé",
            modeles_dispo if modeles_dispo else ["—"],
            key="modele_pretrain",
        )
        algos = ["Ridge", "Huber"] if mode_ml == "Régression" else ["Logistic Regression", "Gradient Boosting"]
        algo_choisi = st.selectbox("Algorithmes", algos, key="algo_choisi")
        nom_modele_default = st.session_state.get("nom_modele_ml", _get_next_model_number())
        nom_modele = st.text_input("Nom modèle", value=nom_modele_default, key="nom_modele_ml", max_chars=30)
        compute_shap = st.checkbox("Calcul SHAP", value=False, key="compute_shap")

    st.divider()

    # --- Popup de confirmation sauvegarde modèle (affiché après entraînement ML) ---
    if st.session_state.get("show_save_dialog"):
        model_path = st.session_state.get("last_trained_model_path", "")
        metrics = st.session_state.get("last_trained_metrics", {})
        mode = st.session_state.get("last_trained_mode", "Régression")

        st.success("✅ Entraînement terminé avec succès !")
        st.info(f"📁 **Modèle enregistré dans :**\n`{model_path}`")

        # Afficher métriques
        col_m1, col_m2, col_m3 = st.columns(3)
        if mode == "Régression":
            col_m1.metric("MAE", f"{metrics.get('MAE', 0):.3f}")
            col_m2.metric("RMSE", f"{metrics.get('RMSE', 0):.3f}")
            col_m3.metric("R²", f"{metrics.get('R2', 0):.3f}")
        else:
            col_m1.metric("Accuracy", f"{metrics.get('accuracy', 0):.2%}")
            col_m2.metric("Precision", f"{metrics.get('precision', 0):.3f}")
            col_m3.metric("F1", f"{metrics.get('f1', 0):.3f}")

        # SHAP calculé ?
        if st.session_state.get("last_trained_shap"):
            st.info("📊 SHAP values calculés (prêts pour visualisation)")

        # Boutons export
        st.markdown("**Exporter les données :**")
        col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
        with col_exp1:
            if st.button("📥 CSV features/labels", key="btn_export_csv"):
                paths = _export_features_labels_csv()
                if paths[0]:
                    st.toast("CSV exportés dans data/exports/")
                else:
                    st.warning("Erreur export CSV")
        with col_exp2:
            if st.button("🗺️ Carte HTML", key="btn_export_html"):
                _state = st.session_state.get("simulation_state")
                _jour = st.session_state.get("jour_actuel", 0)
                html_path = _export_map_html(_state, _jour)
                if html_path:
                    st.toast(f"Carte exportée : {html_path}")
                else:
                    st.warning("Erreur export carte")
        with col_exp3:
            st.code(model_path, language=None)
        with col_exp4:
            if st.button("✓ Fermer", key="btn_close_dialog", type="primary"):
                st.session_state["show_save_dialog"] = False
                st.rerun()
        st.divider()

    # --- Grande ligne centrale : événements | carte | arrondissements ---
    # Mode Prédiction (radio) → droite en 3 colonnes : Arrondissements | Labels | Prédictions
    if mode_radio == "Prédiction":
        col_events, col_map, col_arr, col_label, col_pred = st.columns(
            [RATIO_GAUCHE, RATIO_CARTE, RATIO_ARR, RATIO_REAL, RATIO_PRED]
        )
        cols_droite = [col_arr, col_label, col_pred]
    else:
        col_events, col_map, col_arr = st.columns([RATIO_GAUCHE, RATIO_CARTE, RATIO_DROITE])
        cols_droite = [col_arr]

    # Mode Entraînement : placeholders pour mise à jour sans rerun (carte ne saute pas, zoom conservé)
    microzones = load_microzones()
    state = st.session_state.get("simulation_state")
    jour_actuel = st.session_state.get("jour_actuel", 0)
    total = st.session_state.get("total_jours", 365)
    run_actuel = st.session_state.get("run_actuel", 0)
    ml_training_pct = st.session_state.get("ml_training_pct", 0)
    map_center: Tuple[float, float] = tuple(st.session_state.get("map_center", (48.8566, 2.3522)))  # type: ignore
    map_zoom: int = st.session_state.get("map_zoom", 12)

    # Placeholders events, map, arr : même affichage Prédiction et Entraînement (simulation jour par jour)
    with col_events:
        ph_events = st.empty()
    with col_map:
        # Story 2.4.3.5 — Option afficher/cacher casernes et hôpitaux sur la carte (par défaut cachés)
        st.checkbox(
            "🗺️ Afficher casernes et hôpitaux",
            value=st.session_state.get("show_casernes_hopitaux", False),
            key="show_casernes_hopitaux",
        )
        ph_map = st.empty()
    with col_arr:
        ph_arr = st.empty()
    # Reset flag pour réafficher le selectbox 18 features au prochain run (nouvelle simulation)
    # Story 2.4.5.2 — Init listes morts / blessés graves si absentes (réinitialisées au Lancer)
    if jour_actuel == 0:
        st.session_state["features_18_rendered"] = False
    if "liste_morts" not in st.session_state:
        st.session_state["liste_morts"] = []
    if "liste_blesses_graves" not in st.session_state:
        st.session_state["liste_blesses_graves"] = []
    # Story 2.4.5.1 — Afficher le selectbox 18 features en haut quand jour_actuel >= 7 (rerun / reprise)
    min_jours_entrainement, min_jours_prediction = 7, 28
    show_18_top = (
        (mode_radio == "Entraînement" and jour_actuel >= min_jours_entrainement)
        or (mode_radio == "Prédiction" and jour_actuel >= min_jours_prediction)
    )
    if show_18_top and state is not None:
        st.session_state["features_18_rendered"] = True
        with col_arr:
            from src.services.ml_service import FEATURE_COLUMNS_18

            options_arr = ["—"] + [f"Arr. {arr} ({arrondissement_roman(arr)})" for arr in range(1, 21)]
            idx_sel_top = st.selectbox(
                "Inspecter arrondissement (features semaine dernière)",
                range(len(options_arr)),
                format_func=lambda i: options_arr[i],
                key="inspect_arr_hebdo",
            )
            if idx_sel_top and idx_sel_top > 0:
                arr_sel_top = idx_sel_top
                df_18_top = _get_features_18_semaine_derniere(state, jour_actuel)
                with st.expander(
                    f"Features hebdo (semaine dernière) – Arr. {arr_sel_top} ({arrondissement_roman(arr_sel_top)})",
                    expanded=True,
                ):
                    if df_18_top is not None and not df_18_top.empty:
                        row_arr_top = df_18_top[df_18_top["arrondissement"] == arr_sel_top]
                        if not row_arr_top.empty:
                            for col in FEATURE_COLUMNS_18:
                                val = row_arr_top[col].iloc[0]
                                label = FEATURE_LABELS_18.get(col, col)
                                st.text(f"{label}: {val}")
                        else:
                            st.caption("Aucune donnée pour cet arrondissement cette semaine.")
                    else:
                        st.caption(
                            "Features non disponibles pour la semaine dernière. "
                            "Vérifiez que le fichier limites microzone/arrondissement existe (Story 1.2) "
                            "ou lancez une extraction ML (Prédiction) pour pré-calculer les features."
                        )
                    if st.button("Fermer", key="close_expander_18"):
                        st.session_state["inspect_arr_hebdo"] = 0
                        st.rerun()
    # Story 2.4.5.2 — Morts et blessés graves sous la carte (tous arr., menu déroulant + détail Golden Hour)
    liste_morts = st.session_state.get("liste_morts", [])
    liste_blesses = st.session_state.get("liste_blesses_graves", [])
    if liste_morts or liste_blesses:
        st.caption("Morts et blessés graves (tous arrondissements) — détail Golden Hour")
        col_morts, col_blesses = st.columns(2)
        with col_morts:
            with st.expander("Morts", expanded=bool(liste_morts)):
                if liste_morts:
                    options_morts = [
                        f"J{e['jour']} — Arr. {e['arrondissement']} — {e['microzone_id']} — {e['type_incident']}"
                        for e in liste_morts
                    ]
                    idx_m = st.selectbox(
                        "Choisir un incident mortel",
                        range(len(options_morts)),
                        format_func=lambda i: options_morts[i],
                        key="select_morts_2_4_5_2",
                    )
                    if idx_m is not None and 0 <= idx_m < len(liste_morts):
                        ent = liste_morts[idx_m]
                        with st.expander("Détail Golden Hour", expanded=True):
                            if ent.get("detail_golden_hour") is None:
                                st.caption("N/A — incident issu d’un événement.")
                            else:
                                d = ent["detail_golden_hour"]
                                st.text(f"Microzone : {ent['microzone_id']}")
                                st.text(f"Caserne : {d.get('caserne_id', 'N/A')}")
                                st.text(f"Hôpital : {d.get('hopital_id', 'N/A')}")
                                st.text(f"Temps trajet (min) : {d.get('temps_trajet', 'N/A')}")
                                st.text(f"Temps total (min) : {d.get('temps_total', 'N/A')}")
                                st.text(f"Seuil Golden Hour (min) : {d.get('seuil_golden_hour_minutes', 60)}")
                                st.text(f"Tirage : {d.get('tirage', 'N/A')}")
                                st.text(f"Prob. mort : {d.get('prob_mort', 'N/A')}")
                                st.text(f"Prob. blessé grave : {d.get('prob_blesse_grave', 'N/A')}")
                else:
                    st.caption("Aucun mort pour ce run.")
        with col_blesses:
            with st.expander("Blessés graves", expanded=bool(liste_blesses)):
                if liste_blesses:
                    options_blesses = [
                        f"J{e['jour']} — Arr. {e['arrondissement']} — {e['microzone_id']} — {e['type_incident']}"
                        for e in liste_blesses
                    ]
                    idx_b = st.selectbox(
                        "Choisir un blessé grave",
                        range(len(options_blesses)),
                        format_func=lambda i: options_blesses[i],
                        key="select_blesses_2_4_5_2",
                    )
                    if idx_b is not None and 0 <= idx_b < len(liste_blesses):
                        ent = liste_blesses[idx_b]
                        with st.expander("Détail Golden Hour", expanded=True):
                            if ent.get("detail_golden_hour") is None:
                                st.caption("N/A — incident issu d’un événement.")
                            else:
                                d = ent["detail_golden_hour"]
                                st.text(f"Microzone : {ent['microzone_id']}")
                                st.text(f"Caserne : {d.get('caserne_id', 'N/A')}")
                                st.text(f"Hôpital : {d.get('hopital_id', 'N/A')}")
                                st.text(f"Temps trajet (min) : {d.get('temps_trajet', 'N/A')}")
                                st.text(f"Temps total (min) : {d.get('temps_total', 'N/A')}")
                                st.text(f"Seuil Golden Hour (min) : {d.get('seuil_golden_hour_minutes', 60)}")
                                st.text(f"Tirage : {d.get('tirage', 'N/A')}")
                                st.text(f"Prob. mort : {d.get('prob_mort', 'N/A')}")
                                st.text(f"Prob. blessé grave : {d.get('prob_blesse_grave', 'N/A')}")
                else:
                    st.caption("Aucun blessé grave pour ce run.")
    # Colonne(s) droite(s) — Prédiction : Arrondissements | Prédiction (col 2) | Label réel (col 3)
    ph_col_pred, ph_col_label = None, None
    if mode_radio == "Prédiction":
        # Prédiction auto si état avec 4+ semaines et modèle sélectionné (au chargement ou reprise)
        if state and jour_actuel >= JOURS_PAR_PERIODE and not st.session_state.get("ml_labels_par_periode"):
            modele_choisi = st.session_state.get("modele_pretrain") or st.session_state.get("modele_choisi")
            if modele_choisi and modele_choisi != "—":
                labels_pp, preds_pp, _ = _run_ml_prediction_full(
                    st.session_state.get("mode_ml", "Régression"),
                    modele_choisi,
                    state,
                )
                if labels_pp is not None and preds_pp is not None:
                    st.session_state["ml_labels_par_periode"] = labels_pp
                    st.session_state["ml_preds_par_periode"] = preds_pp
        fly_css = "@keyframes flyaway{0%{opacity:1;transform:translate(0,0) scale(1);}100%{opacity:0;transform:var(--fx) scale(0.8);}}.fly-ecart{animation:flyaway 1.5s ease-out forwards;font-size:1.1rem;font-weight:700;}"
        st.markdown(f"<style>{fly_css}</style>", unsafe_allow_html=True)
        with cols_droite[1]:
            ph_col_pred = st.empty()
        with cols_droite[2]:
            ph_col_label = st.empty()
        _render_prediction_cols(ph_col_pred, ph_col_label, state, jour_actuel, mode_ml, microzones)
        # Story 2.4.5.1 — Inspecter 90 features (arrondissement + période) : expander + tableau + download HTML
        labels_pp = st.session_state.get("ml_labels_par_periode", {})
        if labels_pp and state is not None:
            with st.expander("Inspecter les 90 features ML (arrondissement + période)"):
                mois_options = sorted(labels_pp.keys())
                mois_labels = [f"Période {m} (J{(m-1)*JOURS_PAR_PERIODE}→J{m*JOURS_PAR_PERIODE})" for m in mois_options]
                idx_mois = st.selectbox(
                    "Période (mois)",
                    range(len(mois_options)),
                    format_func=lambda i: mois_labels[i],
                    key="inspect_90_mois",
                )
                arr_90 = st.selectbox(
                    "Arrondissement",
                    options=list(range(1, 21)),
                    format_func=lambda a: f"Arr. {a} ({arrondissement_roman(a)})",
                    key="inspect_90_arr",
                )
                if idx_mois is not None and arr_90 is not None:
                    mois_90 = mois_options[idx_mois]
                    df_ml, feat_cols = _get_90_features_data(state, mode_ml)
                    if df_ml is not None and feat_cols:
                        row_mask = (df_ml["arrondissement"] == arr_90) & (df_ml["mois"] == mois_90)
                        row_df = df_ml.loc[row_mask]
                        if not row_df.empty:
                            row_series = row_df.iloc[0]
                            # Affichage structuré par bloc (Streamlit)
                            blocs_names = [
                                ("Central dernière semaine (sem_m1)", "central_sem_m1_"),
                                ("Central semaine -2 (sem_m2)", "central_sem_m2_"),
                                ("Central semaine -3 (sem_m3)", "central_sem_m3_"),
                                ("Central semaine -4 (sem_m4)", "central_sem_m4_"),
                                ("Voisins (moyenne) dernière semaine", "voisins_moy_sem_m1_"),
                            ]
                            for bloc_name, prefix in blocs_names:
                                cols_in_bloc = [c for c in feat_cols if c.startswith(prefix)]
                                if cols_in_bloc:
                                    st.subheader(bloc_name)
                                    for col in cols_in_bloc:
                                        label = _feature_90_col_to_readable(col)
                                        val = row_series.get(col, "")
                                        st.text(f"{label}: {val}")
                            # Bouton télécharger HTML (ouvrir dans nouvel onglet)
                            html_content = _build_90_features_html_table(
                                row_series, feat_cols, arr_90, mois_90
                            )
                            st.download_button(
                                "Télécharger HTML (ouvrir dans un nouvel onglet)",
                                data=html_content,
                                file_name=f"features_90_arr_{arr_90}_mois_{mois_90}.html",
                                mime="text/html",
                                key="dl_90_features",
                            )
                        else:
                            st.caption("Aucune ligne pour cet arrondissement et cette période.")
                    else:
                        st.caption("Données ML non disponibles pour ce run.")
    # --- Bandeau bas : Jours, Nb jours (même forme pour Entraînement et Prédiction) ---
    nb_runs = st.session_state.get("nb_runs", nb_runs_bandeau)
    ml_table_pct = st.session_state.get("ml_table_pct", 0)

    if mode_radio == "Prédiction":
        b1, b2 = st.columns([2, 6])
        with b1:
            ph_jours = st.empty()
            ph_jours.markdown(f"<small><b>Jours</b> {jour_actuel}/{total}</small>", unsafe_allow_html=True)
        with b2:
            st.markdown(f"<small>Jours: {nb_jours_bandeau}</small>", unsafe_allow_html=True)
        ph_run, ph_table_ml, ph_ml_training = None, None, None
    else:
        b1, b2, b3, b4, b5 = st.columns([2, 2, 2, 2, 4])
        with b1:
            ph_jours = st.empty()
        with b2:
            ph_run = st.empty()
            ph_run.markdown(f"<small><b>Run</b> {run_actuel}/{nb_runs}</small>", unsafe_allow_html=True)
        with b3:
            ph_table_ml = st.empty()
            ph_table_ml.markdown(f"<small><b>Table ML</b> {ml_table_pct}%</small>", unsafe_allow_html=True)
        with b4:
            ph_ml_training = st.empty()
            ph_ml_training.markdown(f"<small><b>ML training</b> {ml_training_pct}%</small>", unsafe_allow_html=True)
        with b5:
            st.markdown(f"<small>Jours: {nb_jours_bandeau} | Runs: {nb_runs_bandeau}</small>", unsafe_allow_html=True)
    if not st.session_state.get("simulation_lancee", False):
        st.session_state["total_jours"] = nb_jours_bandeau

    # Remplir placeholders et boucle simulation (Prédiction et Entraînement : même comportement)
    _render_central_row_and_jours(
        ph_events, ph_map, ph_arr, ph_jours,
        state, jour_actuel, total, run_actuel, ml_training_pct,
        microzones, map_center, map_zoom,
    )

    scenario_ui = st.session_state.get("scenario_ui")
    variabilite_ui = st.session_state.get("variabilite_ui")
    try:
        config_path = str(PathResolver.get_project_root() / "config" / "config.yaml")
        config = load_and_validate_config(config_path)
        run_seed = st.session_state.get("run_seed")
        sim = SimulationService(config=config, seed=run_seed)
        speed_per_day = getattr(getattr(config, "simulation", None), "speed_per_day_seconds", 0.33)
        if not isinstance(speed_per_day, (int, float)) or speed_per_day < 0.01:
            speed_per_day = 0.33
    except Exception:
        config, sim, speed_per_day = None, None, 0.33

    # Boucle simulation jour par jour (Prédiction et Entraînement)
    while (
        st.session_state.get("simulation_lancee")
        and jour_actuel < total
        and state is not None
        and sim is not None
    ):
        sim.advance_one_day(state, scenario_ui=scenario_ui, variabilite_ui=variabilite_ui)
        jour_actuel += 1
        st.session_state["jour_actuel"] = jour_actuel
        st.session_state["simulation_state"] = state
        # Story 2.4.5.2 — Collecter morts et blessés graves (tous arr.) pour le jour qu’on vient de générer
        lm, lb = _collect_casualties_jour(state, jour_actuel - 1)
        st.session_state.setdefault("liste_morts", []).extend(lm)
        st.session_state.setdefault("liste_blesses_graves", []).extend(lb)
        if jour_actuel >= total:
            st.session_state["simulation_lancee"] = False

        # Prédiction auto quand 4 semaines écoulées (28, 56, 84, ...)
        if mode_radio == "Prédiction" and jour_actuel >= JOURS_PAR_PERIODE and jour_actuel % JOURS_PAR_PERIODE == 0:
            modele_choisi = st.session_state.get("modele_pretrain") or st.session_state.get("modele_choisi")
            if modele_choisi and modele_choisi != "—":
                labels_pp, preds_pp, _ = _run_ml_prediction_full(
                    st.session_state.get("mode_ml", "Régression"),
                    modele_choisi,
                    state,
                )
                if labels_pp is not None and preds_pp is not None:
                    st.session_state["ml_labels_par_periode"] = labels_pp
                    st.session_state["ml_preds_par_periode"] = preds_pp

        _render_central_row_and_jours(
            ph_events, ph_map, ph_arr, ph_jours,
            state, jour_actuel, total, run_actuel, ml_training_pct,
            microzones, map_center, map_zoom,
        )
        if mode_radio == "Prédiction" and ph_col_pred is not None and ph_col_label is not None:
            _render_prediction_cols(ph_col_pred, ph_col_label, state, jour_actuel, mode_ml, microzones)
        # Story 2.4.5.1 — Ajouter le selectbox 18 features une seule fois dès J7 (Entraînement) ou J28 (Prédiction)
        min_jours_entrainement, min_jours_prediction = 7, 28
        show_18 = (
            (mode_radio == "Entraînement" and jour_actuel >= min_jours_entrainement)
            or (mode_radio == "Prédiction" and jour_actuel >= min_jours_prediction)
        )
        if (
            show_18
            and state is not None
            and not st.session_state.get("features_18_rendered", False)
        ):
            st.session_state["features_18_rendered"] = True
            with col_arr:
                from src.services.ml_service import FEATURE_COLUMNS_18

                options_arr = ["—"] + [f"Arr. {arr} ({arrondissement_roman(arr)})" for arr in range(1, 21)]
                idx_sel = st.selectbox(
                    "Inspecter arrondissement (features semaine dernière)",
                    range(len(options_arr)),
                    format_func=lambda i: options_arr[i],
                    key="inspect_arr_hebdo",
                )
                if idx_sel and idx_sel > 0:
                    arr_sel = idx_sel
                    df_18 = _get_features_18_semaine_derniere(state, jour_actuel)
                    with st.expander(
                        f"Features hebdo (semaine dernière) – Arr. {arr_sel} ({arrondissement_roman(arr_sel)})",
                        expanded=True,
                    ):
                        if df_18 is not None and not df_18.empty:
                            row_arr = df_18[df_18["arrondissement"] == arr_sel]
                            if not row_arr.empty:
                                for col in FEATURE_COLUMNS_18:
                                    val = row_arr[col].iloc[0]
                                    label = FEATURE_LABELS_18.get(col, col)
                                    st.text(f"{label}: {val}")
                            else:
                                st.caption("Aucune donnée pour cet arrondissement cette semaine.")
                        else:
                            st.caption(
                                "Features non disponibles pour la semaine dernière. "
                                "Vérifiez que le fichier limites microzone/arrondissement existe (Story 1.2) "
                                "ou lancez une extraction ML (Prédiction) pour pré-calculer les features."
                            )
                        if st.button("Fermer", key="close_expander_18"):
                            st.session_state["inspect_arr_hebdo"] = 0
                            st.rerun()
        if jour_actuel >= total:
            break
        time.sleep(speed_per_day)

    # Fin simulation visible : entraînement ML si mode Entraînement
    if jour_actuel >= total and st.session_state.get("ml_training_pending") and mode_radio == "Entraînement":
        st.session_state["ml_training_pending"] = False
        _launch_ml_training_after_visible_run(
            ph_run=ph_run,
            ph_table_ml=ph_table_ml,
            ph_ml_training=ph_ml_training,
        )

    st.caption("Story 2.4.1 — Layout · Entraînement / Prédiction · Tests manuels.")


if __name__ == "__main__":
    main()
