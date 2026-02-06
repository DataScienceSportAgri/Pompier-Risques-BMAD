"""
Validation de configuration avec Pydantic.
Story 2.1.3 - Validation configuration avec Pydantic
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


class PathsConfig(BaseModel):
    """Configuration des chemins de dossiers."""
    
    data_source: str = Field(..., description="Chemin vers data/source_data")
    data_patterns: str = Field(..., description="Chemin vers data/patterns")
    data_intermediate: str = Field(..., description="Chemin vers data/intermediate")
    data_models: str = Field(..., description="Chemin vers data/models")
    scripts: str = Field(..., description="Chemin vers scripts")
    
    @field_validator('data_source', 'data_patterns', 'data_intermediate', 'data_models', 'scripts', mode='before')
    @classmethod
    def validate_paths_exist(cls, v: str) -> str:
        """Valide que les chemins existent (dossiers)."""
        if isinstance(v, str):
            path = Path(v)
            if not path.exists():
                raise ValueError(
                    f"Chemin introuvable: {v}. Le dossier doit exister."
                )
            if not path.is_dir():
                raise ValueError(
                    f"Le chemin n'est pas un dossier: {v}"
                )
        return v


class SimulationConfig(BaseModel):
    """Configuration de la simulation."""
    
    default_days: int = Field(ge=1, le=10000, description="Nombre de jours par défaut")
    default_runs: int = Field(ge=1, le=1000, description="Nombre de runs par défaut")
    speed_per_day_seconds: float = Field(gt=0.0, le=3600.0, description="Vitesse simulation (secondes/jour)")
    seed_default: int = Field(ge=0, description="Seed par défaut pour reproductibilité")


class ScenarioConfig(BaseModel):
    """Configuration d'un scénario (pessimiste, moyen, optimiste)."""
    
    facteur_intensite: float = Field(gt=0.0, le=10.0, description="Facteur d'intensité")
    proba_crise: float = Field(ge=0.0, le=1.0, description="Probabilité de crise")
    variabilite_locale: float = Field(ge=0.0, le=1.0, description="Variabilité locale")


class ScenariosConfig(BaseModel):
    """Configuration des scénarios."""
    
    pessimiste: ScenarioConfig
    moyen: ScenarioConfig
    optimiste: ScenarioConfig
    
    # Validation des scénarios gérée par la structure du modèle


class MicrozonesConfig(BaseModel):
    """Configuration des microzones."""
    
    nombre: int = Field(ge=1, le=1000, description="Nombre de microzones")
    source: str = Field(pattern="^(IRIS|OSM|grille)$", description="Source des microzones")
    aggregation_method: str = Field(default="auto", description="Méthode d'agrégation")


class GoldenHourConfig(BaseModel):
    """Configuration de la Golden Hour."""
    
    seuil_minutes: int = Field(ge=1, le=1440, description="Seuil en minutes")
    facteur_congestion_base: float = Field(gt=0.0, description="Facteur congestion de base")
    facteur_stress_base: float = Field(gt=0.0, description="Facteur stress de base")


class MLConfig(BaseModel):
    """Configuration Machine Learning."""
    
    features_central: int = Field(ge=1, description="Nombre de features centrales")
    features_voisins: int = Field(ge=0, description="Nombre de features par voisin")
    total_features: int = Field(ge=1, description="Total features")
    algorithmes_regression: List[str] = Field(..., description="Algorithmes de régression")
    algorithmes_classification: List[str] = Field(..., description="Algorithmes de classification")
    metrics: Dict[str, List[str]] = Field(..., description="Métriques par type")
    
    @field_validator('algorithmes_regression', 'algorithmes_classification')
    @classmethod
    def validate_algorithms_not_empty(cls, v: List[str]) -> List[str]:
        """Valide que les listes d'algorithmes ne sont pas vides."""
        if not v or len(v) == 0:
            raise ValueError("La liste d'algorithmes ne peut pas être vide")
        return v
    
    @model_validator(mode='after')
    def validate_total_features_coherence(self):
        """Valide la cohérence du total_features."""
        central = self.features_central
        voisins = self.features_voisins
        total = self.total_features
        # Approximation : 1 central + 4 voisins (peut varier)
        expected_min = central + (4 * voisins)
        if total < expected_min:
            raise ValueError(
                f"total_features ({total}) semble trop faible par rapport à "
                f"features_central ({central}) + features_voisins ({voisins})"
            )
        return self


class PrecomputeDistancesConfig(BaseModel):
    """Configuration pré-calcul distances."""
    
    source_casernes: str = Field(pattern="^(internet|file)$", description="Source casernes")
    source_hopitaux: str = Field(pattern="^(internet|file)$", description="Source hôpitaux")
    method: str = Field(pattern="^(geodesic|network)$", description="Méthode de calcul")


class PrecomputeMicrozonesConfig(BaseModel):
    """Configuration pré-calcul microzones."""
    
    source: str = Field(pattern="^(IRIS|OSM|grille)$", description="Source microzones")
    output_format: str = Field(pattern="^(pickle|geojson)$", description="Format de sortie")


class PrecomputeVectorsStaticConfig(BaseModel):
    """Configuration pré-calcul vecteurs statiques."""
    
    patterns_dir: str = Field(..., description="Dossier des patterns")
    default_if_missing: bool = Field(default=True, description="Utiliser valeurs par défaut si manquant")
    
    @field_validator('patterns_dir')
    @classmethod
    def validate_patterns_dir(cls, v: str) -> str:
        """Valide que le dossier patterns existe."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Dossier patterns introuvable: {v}")
        if not path.is_dir():
            raise ValueError(f"Le chemin patterns n'est pas un dossier: {v}")
        return v


class PrecomputePrixM2Config(BaseModel):
    """Configuration pré-calcul prix m²."""
    
    source: str = Field(pattern="^(internet|generated|internet_or_generated)$", description="Source prix m²")
    fallback_generation: bool = Field(default=True, description="Génération de fallback")


class PrecomputeCongestionStaticConfig(BaseModel):
    """Configuration pré-calcul congestion statique."""
    
    include_seasonality: bool = Field(default=True, description="Inclure saisonnalité")
    base_factors: bool = Field(default=True, description="Facteurs de base")


class VecteursStatiquesConfig(BaseModel):
    """Configuration du lissage des vecteurs statiques (Story 2.4.3.1)."""
    lissage_alpha: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Alpha de lissage : 1=aucun, 0.7≈−30% disparité entre microzones",
    )


class MatricesBaseConfig(BaseModel):
    """Configuration des matrices de base (gravité, croisée, voisins) pour la génération J→J+1."""

    reduction_effet: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="0.8 = 80 % réduction ; 0 = effet plein ; négatif = amplification (ex. -0.5 = +50 %)",
    )


class EffetsPatternsConfig(BaseModel):
    """Configuration des effets des patterns de modulation (4j, 7j, 60j) — SANS réaléatoirisation."""

    reduction_effet: float = Field(
        default=0.8,
        ge=-1.0,
        le=1.0,
        description="0.8 = 80 % réduction (20 % conservé) ; 0 = effet plein ; négatif = amplification (ex. -0.5 = 50 % en plus)",
    )


class RealaléatoirisationConfig(BaseModel):
    """Configuration des patterns de réaléatoirisation (Story 2.4.3.4)."""

    enabled: bool = Field(default=True, description="Activer la réaléatoirisation")
    reduction_base_matrices: Optional[float] = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="[Déprécié — utiliser matrices_base.reduction_effet] Fallback si matrices_base absent",
    )
    periode_moyenne_jours: Tuple[int, int] = Field(
        default=(7, 12),
        description="(min, max) jours entre deux déclenchements par arrondissement (Story : 7 à 12 j)",
    )
    duree_pattern_jours: Tuple[int, int] = Field(
        default=(15, 20),
        description="(min, max) durée totale d'un pattern en jours",
    )
    duree_rampe_jours: Tuple[int, int] = Field(
        default=(2, 4),
        description="(min, max) durée de chaque rampe (début, milieu, fin) en jours",
    )
    taux_reduction_min: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Réduction minimale au plateau (60 %)",
    )
    taux_reduction_max: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Réduction maximale au plateau (85 %)",
    )
    max_patterns_simultanes_par_arrondissement: int = Field(
        default=4,
        ge=1,
        le=4,
        description="Nombre max de patterns actifs simultanément par arrondissement (Story : 4)",
    )


class PrecomputeConfig(BaseModel):
    """Configuration pré-calculs."""
    
    enabled: Dict[str, bool] = Field(..., description="Activation/désactivation des blocs")
    distances: Optional[PrecomputeDistancesConfig] = None
    microzones: Optional[PrecomputeMicrozonesConfig] = None
    vectors_static: Optional[PrecomputeVectorsStaticConfig] = None
    prix_m2: Optional[PrecomputePrixM2Config] = None
    congestion_static: Optional[PrecomputeCongestionStaticConfig] = None
    
    @field_validator('enabled')
    @classmethod
    def validate_enabled_keys(cls, v: Dict[str, bool]) -> Dict[str, bool]:
        """Valide que les clés enabled correspondent aux sections."""
        expected_keys = {'distances', 'microzones', 'vectors_static', 'prix_m2', 'congestion_static'}
        provided_keys = set(v.keys())
        if not provided_keys.issubset(expected_keys):
            extra = provided_keys - expected_keys
            raise ValueError(f"Clés inattendues dans 'enabled': {extra}")
        return v


class Config(BaseModel):
    """
    Configuration complète du projet.
    
    Valide la structure, les types, les plages de valeurs, les chemins et la cohérence.
    """
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    paths: PathsConfig
    simulation: SimulationConfig
    scenarios: ScenariosConfig
    vecteurs_statiques: Optional[VecteursStatiquesConfig] = None
    matrices_base: Optional[MatricesBaseConfig] = None
    effets_patterns: Optional[EffetsPatternsConfig] = None
    realaléatoirisation: Optional[RealaléatoirisationConfig] = None
    microzones: MicrozonesConfig
    golden_hour: GoldenHourConfig
    ml: MLConfig
    precompute: PrecomputeConfig

    @model_validator(mode='after')
    def validate_microzones_source_coherence(self):
        """Valide la cohérence de la source microzones avec precompute."""
        if self.precompute and self.precompute.microzones:
            if self.microzones.source != self.precompute.microzones.source:
                raise ValueError(
                    f"Incohérence source microzones: "
                    f"microzones.source={self.microzones.source} vs "
                    f"precompute.microzones.source={self.precompute.microzones.source}"
                )
        return self


def load_and_validate_config(config_path: str) -> Config:
    """
    Charge et valide un fichier de configuration YAML.
    
    Args:
        config_path: Chemin vers le fichier config.yaml
    
    Returns:
        Instance de Config validée
    
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        ValidationError: Si la validation échoue (avec messages d'erreur clairs)
        ValueError: Si le fichier YAML est invalide
    """
    import yaml
    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier de configuration introuvable: {config_path}"
        )
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Erreur de parsing YAML: {e}") from e
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du fichier: {e}") from e
    
    if config_dict is None:
        raise ValueError("Le fichier de configuration est vide")
    
    try:
        return Config(**config_dict)
    except ValidationError as e:
        # Améliorer les messages d'erreur
        errors = []
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error['loc'])
            msg = error['msg']
            error_type = error['type']
            
            if error_type == 'value_error.missing':
                errors.append(f"Champ manquant: {field_path}")
            elif error_type == 'value_error.str.regex':
                errors.append(
                    f"Valeur invalide pour '{field_path}': {msg}. "
                    f"Valeur reçue: {error.get('ctx', {}).get('pattern', 'N/A')}"
                )
            elif error_type == 'type_error':
                errors.append(
                    f"Type incorrect pour '{field_path}': {msg}. "
                    f"Type attendu: {error.get('type', 'N/A')}"
                )
            else:
                errors.append(f"Erreur dans '{field_path}': {msg}")
        
        error_message = "Erreurs de validation de configuration:\n" + "\n".join(f"  - {err}" for err in errors)
        raise ValidationError(error_message, model=Config) from e


def validate_config_dict(config_dict: Dict) -> Config:
    """
    Valide un dictionnaire de configuration.
    
    Args:
        config_dict: Dictionnaire de configuration
    
    Returns:
        Instance de Config validée
    
    Raises:
        ValidationError: Si la validation échoue
    """
    try:
        return Config(**config_dict)
    except ValidationError as e:
        # Même amélioration des messages d'erreur
        errors = []
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error['loc'])
            msg = error['msg']
            errors.append(f"Erreur dans '{field_path}': {msg}")
        
        error_message = "Erreurs de validation de configuration:\n" + "\n".join(f"  - {err}" for err in errors)
        raise ValidationError(error_message, model=Config) from e
