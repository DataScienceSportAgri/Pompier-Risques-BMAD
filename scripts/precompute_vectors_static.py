"""
Pré-calcul des vecteurs statiques, prix m², chômage, délinquance et congestion statique (Story 1.3).

Ce module calcule :
- Vecteurs statiques (3×3 par microzone) à partir des patterns Paris
- Prix m² par microzone (téléchargé depuis internet)
- Chômage par microzone (téléchargé depuis internet)
- Délinquance par microzone (téléchargé depuis internet)
- Congestion statique de base par microzone
"""

import logging
import pickle
from pathlib import Path
from typing import Dict, Tuple, List
import hashlib
import random
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import requests
import json
import io

logger = logging.getLogger(__name__)


class DataDownloader:
    """
    Fournit des données socio-économiques (prix m², chômage, délinquance).

    Contrainte projet (demandée): on **ne dépend pas d'un téléchargement** fiable.
    On génère donc des DataFrames "bruts" **au niveau microzone** (MZxxx), à partir :
    - d'hypothèses réalistes par arrondissement (dicos en dur),
    - de quelques cas particuliers commentés,
    - d'une variation légère et déterministe par microzone (sans commentaires).
    """
    
    def __init__(self, config: Dict):
        self.config = config
    
    # -----------------------------
    # Hypothèses "en dur" (arrond.)
    # -----------------------------
    # Prix m² moyens par arrondissement (approx. Paris intra-muros).
    # Hypothèse: hyper-centre / ouest plus cher ; est/nord-est moins cher.
    #
    # Sources d'inspiration (ordre de grandeur, pas un import direct):
    # - 7e: fourchettes ~13–16k€/m², 6e ~14–15k€/m², 1er ~11.5–13.4k€/m² (micro-quartiers) :
    #   https://magazine.bellesdemeures.com/luxe/destinations/l-arrondissement-plus-riche-de-paris-article-21988_2.html
    # - 7e autour de ~15.1k€/m² (janv 2026) : https://ma-renta.fr/articles/ville/ile-de-france-paris-analyse-immobilier-prix-paris-7e-arrondissement-75107
    # - 16e ~11.0k€/m² (référence 2025, ordre de grandeur) : https://www.seloger.com/prix-de-l-immo/vente/ile-de-france/paris/paris-16eme/750116.htm
    PRIX_M2_PAR_ARR = {
        1: 12500, 2: 11800, 3: 12000, 4: 12500, 5: 12750,
        6: 14800, 7: 15200, 8: 14500, 9: 11200, 10: 10500,
        11: 10800, 12: 10100, 13: 9650, 14: 10700, 15: 11200,
        16: 11100, 17: 10900, 18: 9800, 19: 9400, 20: 9200
    }

    # Taux de chômage moyens (approx. en %), sources T2–T4 2024, T2–T3 2025.
    # 1er–8e: 5.5–6.1 % ; 9e, 15e, 19e: 7.3 % ; 10e–14e, 17e, 20e: 6.5–7.0 % ; 16e: 5.8 % ; 18e: interpolé.
    CHOMAGE_PAR_ARR = {
        1: 5.8, 2: 5.9, 3: 6.1, 4: 5.8, 5: 5.7,
        6: 5.6, 7: 5.5, 8: 5.8, 9: 7.3, 10: 6.5,
        11: 6.7, 12: 6.8, 13: 6.9, 14: 6.6, 15: 7.3,
        16: 5.8, 17: 7.0, 18: 7.1, 19: 7.3, 20: 6.9
    }

    # Indice délinquance (0-100) par arrondissement (approx.).
    # Hypothèse: plus faible ouest/centre, plus élevé nord-est.
    DELINQUANCE_PAR_ARR = {
        1: 45, 2: 50, 3: 55, 4: 60, 5: 40,
        6: 35, 7: 30, 8: 40, 9: 65, 10: 75,
        11: 70, 12: 65, 13: 80, 14: 50, 15: 45,
        16: 35, 17: 55, 18: 85, 19: 90, 20: 95
    }

    # -----------------------------
    # Cas particuliers (microzones)
    # -----------------------------
    # Quelques microzones "emblématiques" (commentées). Ces IDs dépendent du découpage
    # (ici: grille par arrondissement). Si l'ID n'existe pas, l'override est ignoré.
    # Hyper-centre (touristique / premium) → prix m² plus élevé.
    PRIX_M2_OVERRIDES_MZ = {
        # Exemple: microzone très centrale → premium
        "MZ025": 15000,
        "MZ026": 14500,
    }

    # Zone "populaire" → chômage / délinquance un peu plus élevés.
    CHOMAGE_OVERRIDES_MZ = {
        # Exemple: microzone nord-est → chômage un peu au-dessus du voisinage
        "MZ090": 12.5,
        "MZ095": 13.0,
    }

    DELINQUANCE_OVERRIDES_MZ = {
        # Exemple: microzone très fréquentée/animée → indice un peu plus haut
        "MZ070": 88,
        "MZ084": 82,
    }

    def download_prix_m2(self, output_dir: Path, microzones: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        Construit un DataFrame prix m² par microzone (MZxxx), sans téléchargement.

        Returns:
            DataFrame avec colonnes: microzone_id, arrondissement, prix_m2
        """
        return self._generate_metric_by_microzone(
            microzones=microzones,
            base_by_arr=self.PRIX_M2_PAR_ARR,
            overrides_by_mz=self.PRIX_M2_OVERRIDES_MZ,
            column_name="prix_m2",
            jitter_pct=0.06,  # +/-6% de variation intra-arrondissement
            clamp_min=3500,
            clamp_max=22000,
        )

    def download_chomage(self, output_dir: Path, microzones: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        Construit un DataFrame chômage (%) par microzone (MZxxx), sans téléchargement.

        Returns:
            DataFrame avec colonnes: microzone_id, arrondissement, taux_chomage
        """
        return self._generate_metric_by_microzone(
            microzones=microzones,
            base_by_arr=self.CHOMAGE_PAR_ARR,
            overrides_by_mz=self.CHOMAGE_OVERRIDES_MZ,
            column_name="taux_chomage",
            jitter_pct=0.10,  # +/-10% de variation intra-arrondissement
            clamp_min=2.5,
            clamp_max=18.0,
        )

    def download_delinquance(self, output_dir: Path, microzones: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        Construit un DataFrame délinquance (indice 0-100) par microzone (MZxxx), sans téléchargement.

        Returns:
            DataFrame avec colonnes: microzone_id, arrondissement, indice_delinquance
        """
        return self._generate_metric_by_microzone(
            microzones=microzones,
            base_by_arr=self.DELINQUANCE_PAR_ARR,
            overrides_by_mz=self.DELINQUANCE_OVERRIDES_MZ,
            column_name="indice_delinquance",
            jitter_pct=0.08,  # +/-8% de variation intra-arrondissement
            clamp_min=10,
            clamp_max=100,
            as_int=True,
        )

    def _stable_jitter_factor(self, microzone_id: str, jitter_pct: float) -> float:
        """
        Variation légère déterministe autour de 1.0.
        Ex: jitter_pct=0.06 → facteur dans [0.94, 1.06]
        """
        h = hashlib.sha256(microzone_id.encode("utf-8")).hexdigest()
        # Prendre 8 hex digits → int
        seed = int(h[:8], 16)
        rng = random.Random(seed)
        return 1.0 + rng.uniform(-jitter_pct, jitter_pct)

    def _generate_metric_by_microzone(
        self,
        microzones: gpd.GeoDataFrame,
        base_by_arr: Dict[int, float],
        overrides_by_mz: Dict[str, float],
        column_name: str,
        jitter_pct: float,
        clamp_min: float,
        clamp_max: float,
        as_int: bool = False,
    ) -> pd.DataFrame:
        """
        Génère un DataFrame au niveau microzone, à partir d'un niveau arrondissement,
        avec légère variation intra-arrondissement.
        """
        if microzones is None or len(microzones) == 0:
            raise ValueError("microzones est requis pour générer des données par microzone")

        rows = []
        for _, mz in microzones.iterrows():
            microzone_id = mz["microzone_id"]
            arrondissement = int(mz["arrondissement"])

            base_val = float(base_by_arr.get(arrondissement, np.nan))
            if np.isnan(base_val):
                # fallback raisonnable si jamais
                base_val = float(np.mean(list(base_by_arr.values())))

            # Cas particuliers microzones (si l'ID existe)
            if microzone_id in overrides_by_mz:
                val = float(overrides_by_mz[microzone_id])
            else:
                val = base_val * self._stable_jitter_factor(microzone_id, jitter_pct=jitter_pct)

            # Clamp pour rester plausible
            val = max(clamp_min, min(clamp_max, val))
            if as_int:
                val = int(round(val))

            rows.append(
                {
                    "microzone_id": microzone_id,
                    "arrondissement": arrondissement,
                    column_name: val,
                }
            )

        df = pd.DataFrame(rows)
        logger.info(f"✅ {column_name} généré pour {len(df)} microzones")
        return df


class VectorsStaticCalculator:
    """Calcule les vecteurs statiques à partir des patterns et données socio-économiques."""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def load_patterns(self, patterns_dir: Path) -> Dict:
        """Charge les patterns Paris depuis data/patterns/ (format docs/patterns-reference.md)."""
        logger.info(f"📂 Chargement des patterns depuis {patterns_dir}...")
        
        patterns = {}
        pattern_files = {
            'pattern_4j': 'pattern_4j_example.json',
            'pattern_7j': 'pattern_7j_example.json',
            'pattern_60j': 'pattern_60j_example.json'
        }
        
        for pattern_name, filename in pattern_files.items():
            pattern_file = patterns_dir / filename
            if pattern_file.exists():
                try:
                    with open(pattern_file, 'r', encoding='utf-8') as f:
                        patterns[pattern_name] = json.load(f)
                    logger.info(f"✅ Pattern {pattern_name} chargé")
                except Exception as e:
                    logger.warning(f"⚠️  Erreur chargement {pattern_name}: {e}")
            else:
                logger.warning(f"⚠️  Fichier pattern non trouvé: {pattern_file}")
        
        # Si aucun pattern n'est chargé, utiliser des valeurs par défaut
        if not patterns:
            logger.warning("⚠️  Aucun pattern chargé, utilisation de valeurs par défaut")
            patterns = self._get_default_patterns()
        
        return patterns
    
    def _extract_base_probs_from_ref(self, raw: Dict) -> Dict[str, Dict[str, float]]:
        """
        Extrait les probabilite_base du format référence (microzones[].patterns).
        Utilise la première microzone comme template. Voir docs/patterns-reference.md.
        """
        if not raw or "microzones" not in raw or not raw["microzones"]:
            return {}
        m = raw["microzones"][0]
        pa = m.get("patterns", {})
        out: Dict[str, Dict[str, float]] = {}
        for t in ("agressions", "incendies", "accidents"):
            out[t] = {}
            for g in ("benin", "moyen", "grave"):
                bl = pa.get(t, {}).get(g, {})
                default = 0.1 if g == "benin" else (0.05 if g == "moyen" else 0.01)
                out[t][g] = float(bl.get("probabilite_base", default))
        return out
    
    def _get_default_patterns(self) -> Dict:
        """Retourne des patterns par défaut si aucun fichier n'est trouvé."""
        return {
            'pattern_4j': {
                'agressions': {'benin': 0.1, 'moyen': 0.05, 'grave': 0.01},
                'incendies': {'benin': 0.15, 'moyen': 0.08, 'grave': 0.02},
                'accidents': {'benin': 0.2, 'moyen': 0.1, 'grave': 0.03}
            },
            'pattern_7j': {
                'agressions': {'benin': 0.12, 'moyen': 0.06, 'grave': 0.015},
                'incendies': {'benin': 0.18, 'moyen': 0.09, 'grave': 0.025},
                'accidents': {'benin': 0.22, 'moyen': 0.11, 'grave': 0.035}
            },
            'pattern_60j': {
                'agressions': {'benin': 0.1, 'moyen': 0.05, 'grave': 0.01},
                'incendies': {'benin': 0.15, 'moyen': 0.08, 'grave': 0.02},
                'accidents': {'benin': 0.2, 'moyen': 0.1, 'grave': 0.03}
            }
        }
    
    def calculate_vecteurs_statiques(
        self,
        microzones: gpd.GeoDataFrame,
        patterns: Dict,
        prix_m2: pd.DataFrame,
        chomage: pd.DataFrame,
        delinquance: pd.DataFrame
    ) -> Dict[str, Dict[str, Tuple[int, int, int]]]:
        """
        Calcule les vecteurs statiques (3×3 par microzone).
        
        Returns:
            Dict[microzone_id, Dict[type_incident, tuple(bénin, moyen, grave)]]
        """
        logger.info("🔄 Calcul des vecteurs statiques...")
        
        vecteurs = {}
        
        for idx, mz in microzones.iterrows():
            microzone_id = mz['microzone_id']
            arrondissement = int(mz['arrondissement'])
            
            # Récupérer les données socio-économiques pour cette microzone
            prix_m2_mz = self._get_value_for_microzone(prix_m2, microzone_id, arrondissement, 'prix_m2', default=8000)
            taux_chomage = self._get_value_for_microzone(chomage, microzone_id, arrondissement, 'taux_chomage', default=7.0)
            indice_delinquance = self._get_value_for_microzone(delinquance, microzone_id, arrondissement, 'indice_delinquance', default=60)
            
            # Facteurs de modulation selon données socio-économiques
            facteur_prix = prix_m2_mz / 8000  # Normalisation autour de 8000€/m²
            facteur_chomage = taux_chomage / 7.0  # Normalisation autour de 7%
            facteur_delinquance = indice_delinquance / 60  # Normalisation autour de 60
            
            vecteurs[microzone_id] = {}
            
            # Pour chaque type d'incident
            # Pattern 60j comme base (long terme). Format référence (microzones[].patterns)
            # ou défauts si absent / format inconnu. Voir docs/patterns-reference.md.
            base_60 = patterns.get('pattern_60j')
            if base_60 and isinstance(base_60, dict) and 'microzones' in base_60:
                base_probs = self._extract_base_probs_from_ref(base_60)
            else:
                base_probs = self._get_default_patterns()['pattern_60j']
            
            for incident_type in ['agressions', 'incendies', 'accidents']:
                pattern_base = base_probs.get(incident_type, {})
                prob_benin = pattern_base.get('benin', 0.1)
                prob_moyen = pattern_base.get('moyen', 0.05)
                prob_grave = pattern_base.get('grave', 0.01)
                
                # Modulation selon le type d'incident
                if incident_type == 'agressions':
                    # Agressions: influencées par délinquance et chômage
                    prob_benin *= (1 + 0.3 * (facteur_delinquance - 1))
                    prob_moyen *= (1 + 0.4 * (facteur_delinquance - 1))
                    prob_grave *= (1 + 0.5 * (facteur_delinquance - 1))
                    # Prix m²: zones chères = moins d'agressions
                    facteur_prix_agression = 1 / facteur_prix
                    prob_benin *= facteur_prix_agression
                    prob_moyen *= facteur_prix_agression
                    prob_grave *= facteur_prix_agression
                
                elif incident_type == 'incendies':
                    # Incendies: influencés par densité (approximée par prix m²)
                    prob_benin *= (1 + 0.2 * (facteur_prix - 1))
                    prob_moyen *= (1 + 0.3 * (facteur_prix - 1))
                    prob_grave *= (1 + 0.4 * (facteur_prix - 1))
                
                elif incident_type == 'accidents':
                    # Accidents: influencés par trafic (approximé par prix m² et chômage)
                    prob_benin *= (1 + 0.1 * (facteur_prix - 1))
                    prob_moyen *= (1 + 0.15 * (facteur_prix - 1))
                    prob_grave *= (1 + 0.2 * (facteur_prix - 1))
                
                # Convertir probabilités en valeurs entières (vecteurs)
                # Multiplier par un facteur d'échelle pour avoir des valeurs réalistes
                facteur_echelle = 100
                benin = max(0, int(prob_benin * facteur_echelle))
                moyen = max(0, int(prob_moyen * facteur_echelle))
                grave = max(0, int(prob_grave * facteur_echelle))
                
                vecteurs[microzone_id][incident_type] = (benin, moyen, grave)
        
        logger.info(f"✅ Vecteurs statiques calculés pour {len(vecteurs)} microzones")
        return vecteurs
    
    def _get_value_for_microzone(
        self,
        df: pd.DataFrame,
        microzone_id: str,
        arrondissement: int,
        column: str,
        default: float
    ) -> float:
        """Récupère une valeur pour une microzone depuis un DataFrame (fallback arrondissement)."""
        if df is None:
            return default
        if 'microzone_id' in df.columns:
            filtered = df[df['microzone_id'] == microzone_id]
            if len(filtered) > 0 and column in filtered.columns:
                return float(filtered[column].iloc[0])
        if 'arrondissement' in df.columns:
            filtered = df[df['arrondissement'] == arrondissement]
            if len(filtered) > 0 and column in filtered.columns:
                return float(filtered[column].iloc[0])
        return default


class CongestionStaticCalculator:
    """Calcule la congestion statique de base par microzone."""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def calculate_congestion_static(
        self,
        microzones: gpd.GeoDataFrame,
        prix_m2: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calcule la congestion statique de base par microzone.
        
        Facteurs statiques:
        - Saisonnalité (intersaison > hiver/été)
        - Caractéristiques microzone (densité, prix m²)
        
        Returns:
            DataFrame avec colonnes: microzone_id, congestion_base_hiver, congestion_base_ete, congestion_base_intersaison
        """
        logger.info("🔄 Calcul de la congestion statique de base...")
        
        congestion_data = []
        
        for idx, mz in microzones.iterrows():
            microzone_id = mz['microzone_id']
            arrondissement = int(mz['arrondissement'])
            
            # Récupérer prix m² (proxy de densité)
            prix_m2_mz = self._get_value_for_microzone(prix_m2, microzone_id, arrondissement, 'prix_m2', default=8000)
            
            # Facteur de base selon densité (prix m²)
            facteur_densite = prix_m2_mz / 8000  # Normalisation
            
            # Congestion de base par saison
            # Intersaison > hiver/été (plus de trafic en intersaison)
            congestion_base = 1.0 * facteur_densite
            
            congestion_hiver = congestion_base * 0.9  # Moins de trafic en hiver
            congestion_ete = congestion_base * 0.85   # Moins de trafic en été (vacances)
            congestion_intersaison = congestion_base * 1.1  # Plus de trafic en intersaison
            
            congestion_data.append({
                'microzone_id': microzone_id,
                'arrondissement': arrondissement,
                'congestion_base_hiver': congestion_hiver,
                'congestion_base_ete': congestion_ete,
                'congestion_base_intersaison': congestion_intersaison,
                'facteur_densite': facteur_densite
            })
        
        df_congestion = pd.DataFrame(congestion_data)
        logger.info(f"✅ Congestion statique calculée pour {len(df_congestion)} microzones")
        return df_congestion
    
    def _get_value_for_microzone(
        self,
        df: pd.DataFrame,
        microzone_id: str,
        arrondissement: int,
        column: str,
        default: float
    ) -> float:
        """Récupère une valeur pour une microzone (fallback arrondissement)."""
        if df is None:
            return default
        if 'microzone_id' in df.columns:
            filtered = df[df['microzone_id'] == microzone_id]
            if len(filtered) > 0 and column in filtered.columns:
                return float(filtered[column].iloc[0])
        if 'arrondissement' in df.columns:
            filtered = df[df['arrondissement'] == arrondissement]
            if len(filtered) > 0 and column in filtered.columns:
                return float(filtered[column].iloc[0])
        return default


def precompute_vectors_static(config: Dict, output_dir: Path) -> bool:
    """
    Fonction principale de pré-calcul des vecteurs statiques, prix m² et congestion.
    
    Returns:
        True si succès, False sinon
    """
    try:
        # 1. Charger les microzones
        logger.info("📂 Chargement des microzones...")
        microzones_file = output_dir / "microzones.pkl"
        if not microzones_file.exists():
            logger.error(f"❌ Fichier microzones introuvable: {microzones_file}")
            logger.error("   Exécutez d'abord: python scripts/run_precompute.py --only-distances")
            return False
        
        with open(microzones_file, 'rb') as f:
            microzones = pickle.load(f)
        
        logger.info(f"✅ {len(microzones)} microzones chargées")
        
        # 2. Télécharger les données depuis internet
        downloader = DataDownloader(config)
        
        prix_m2 = downloader.download_prix_m2(output_dir, microzones)
        chomage = downloader.download_chomage(output_dir, microzones)
        delinquance = downloader.download_delinquance(output_dir, microzones)
        
        # Sauvegarder les données brutes
        prix_m2_file = output_dir / "prix_m2.pkl"
        with open(prix_m2_file, 'wb') as f:
            pickle.dump(prix_m2, f)
        logger.info(f"✅ Prix m² sauvegardés: {prix_m2_file}")
        
        chomage_file = output_dir / "chomage.pkl"
        with open(chomage_file, 'wb') as f:
            pickle.dump(chomage, f)
        logger.info(f"✅ Chômage sauvegardé: {chomage_file}")
        
        delinquance_file = output_dir / "delinquance.pkl"
        with open(delinquance_file, 'wb') as f:
            pickle.dump(delinquance, f)
        logger.info(f"✅ Délinquance sauvegardée: {delinquance_file}")
        
        # 3. Charger les patterns
        patterns_dir = Path(config['paths']['data_patterns'])
        if not patterns_dir.is_absolute():
            patterns_dir = Path(__file__).parent.parent / patterns_dir
        patterns_dir.mkdir(parents=True, exist_ok=True)
        
        calculator = VectorsStaticCalculator(config)
        patterns = calculator.load_patterns(patterns_dir)
        
        # 4. Calculer les vecteurs statiques
        vecteurs_statiques = calculator.calculate_vecteurs_statiques(
            microzones, patterns, prix_m2, chomage, delinquance
        )
        
        vecteurs_file = output_dir / "vecteurs_statiques.pkl"
        with open(vecteurs_file, 'wb') as f:
            pickle.dump(vecteurs_statiques, f)
        logger.info(f"✅ Vecteurs statiques sauvegardés: {vecteurs_file}")
        
        # 5. Calculer la congestion statique
        congestion_calc = CongestionStaticCalculator(config)
        congestion_static = congestion_calc.calculate_congestion_static(microzones, prix_m2)
        
        congestion_file = output_dir / "congestion_statique.pkl"
        with open(congestion_file, 'wb') as f:
            pickle.dump(congestion_static, f)
        logger.info(f"✅ Congestion statique sauvegardée: {congestion_file}")
        
        # 6. Vérifications
        logger.info("🔍 Vérifications...")
        
        # Vérifier dimensions vecteurs statiques
        assert len(vecteurs_statiques) == len(microzones), \
            f"Nombre de microzones incorrect dans vecteurs: {len(vecteurs_statiques)} (attendu: {len(microzones)})"
        
        for mz_id, vecteurs in vecteurs_statiques.items():
            assert len(vecteurs) == 3, f"Nombre de types d'incidents incorrect pour {mz_id}"
            for incident_type, vector in vecteurs.items():
                assert len(vector) == 3, f"Vecteur {incident_type} pour {mz_id} doit avoir 3 valeurs"
                assert all(v >= 0 for v in vector), f"Valeurs négatives dans vecteur {incident_type} pour {mz_id}"
        
        # Vérifier congestion statique
        assert len(congestion_static) == len(microzones), \
            f"Nombre de microzones incorrect dans congestion: {len(congestion_static)} (attendu: {len(microzones)})"
        assert all(congestion_static['congestion_base_intersaison'] > congestion_static['congestion_base_hiver']), \
            "Congestion intersaison doit être > hiver"
        assert all(congestion_static['congestion_base_intersaison'] > congestion_static['congestion_base_ete']), \
            "Congestion intersaison doit être > été"
        
        logger.info("✅ Toutes les vérifications passées")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur pré-calcul vecteurs statiques: {e}", exc_info=True)
        return False
