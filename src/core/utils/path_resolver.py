"""
Système centralisé de résolution de chemins.
Story 2.1.4 - Système centralisé de résolution de chemins

Tous les chemins sont relatifs à la racine du projet.
Convention de nommage standardisée pour faciliter la maintenance.
"""

from pathlib import Path
from typing import Optional


class PathResolver:
    """
    Système centralisé de résolution de chemins relatifs à la racine du projet.
    
    Tous les chemins sont résolus depuis la racine du projet (où se trouve le README.md).
    """
    
    # Racine du projet (détectée automatiquement)
    _project_root: Optional[Path] = None
    
    @classmethod
    def get_project_root(cls) -> Path:
        """
        Détecte et retourne la racine du projet.
        
        La racine est identifiée par la présence de fichiers caractéristiques :
        - README.md
        - config/config.yaml
        - .git (si git est utilisé)
        
        Returns:
            Path vers la racine du projet
        
        Raises:
            RuntimeError: Si la racine du projet ne peut pas être détectée
        """
        if cls._project_root is not None:
            return cls._project_root
        
        # Commencer depuis le fichier actuel et remonter
        current = Path(__file__).resolve()
        
        # Remonter jusqu'à trouver la racine (max 10 niveaux)
        for _ in range(10):
            # Vérifier les indicateurs de racine
            if (current / "README.md").exists() and (current / "config" / "config.yaml").exists():
                cls._project_root = current
                return cls._project_root
            
            parent = current.parent
            if parent == current:  # On est à la racine du système de fichiers
                break
            current = parent
        
        # Si pas trouvé, essayer depuis le répertoire de travail courant
        cwd = Path.cwd()
        if (cwd / "README.md").exists() and (cwd / "config" / "config.yaml").exists():
            cls._project_root = cwd
            return cls._project_root
        
        raise RuntimeError(
            "Impossible de détecter la racine du projet. "
            "Assurez-vous que README.md et config/config.yaml existent."
        )
    
    @classmethod
    def resolve(cls, *path_parts: str) -> Path:
        """
        Résout un chemin relatif depuis la racine du projet.
        
        Args:
            *path_parts: Parties du chemin (peut être plusieurs arguments ou un seul chemin)
        
        Returns:
            Path absolu résolu
        
        Examples:
            >>> PathResolver.resolve("data", "source_data", "microzones.pkl")
            Path("/path/to/project/data/source_data/microzones.pkl")
            
            >>> PathResolver.resolve("config/config.yaml")
            Path("/path/to/project/config/config.yaml")
        """
        root = cls.get_project_root()
        
        # Si un seul argument avec des séparateurs, le traiter comme un chemin
        if len(path_parts) == 1 and ("/" in path_parts[0] or "\\" in path_parts[0]):
            path_str = path_parts[0]
            # Normaliser les séparateurs
            path_str = path_str.replace("\\", "/")
            parts = path_str.split("/")
        else:
            parts = list(path_parts)
        
        # Construire le chemin depuis la racine
        resolved = root
        for part in parts:
            if part:  # Ignorer les parties vides
                resolved = resolved / part
        
        return resolved.resolve()
    
    @classmethod
    def data_source(cls, filename: str) -> Path:
        """
        Résout un chemin vers data/source_data.
        
        Args:
            filename: Nom du fichier (ex: "microzones.pkl")
        
        Returns:
            Path vers le fichier dans data/source_data
        """
        return cls.resolve("data", "source_data", filename)
    
    @classmethod
    def data_patterns(cls, filename: str) -> Path:
        """
        Résout un chemin vers data/patterns.
        
        Args:
            filename: Nom du fichier (ex: "pattern_7j_example.json")
        
        Returns:
            Path vers le fichier dans data/patterns
        """
        return cls.resolve("data", "patterns", filename)
    
    @classmethod
    def data_intermediate(cls, *path_parts: str) -> Path:
        """
        Résout un chemin vers data/intermediate.
        
        Args:
            *path_parts: Parties du chemin (ex: "run_001", "vectors.pkl")
        
        Returns:
            Path vers le fichier/dossier dans data/intermediate
        """
        return cls.resolve("data", "intermediate", *path_parts)
    
    @classmethod
    def data_models(cls, filename: str) -> Path:
        """
        Résout un chemin vers data/models.
        
        Args:
            filename: Nom du fichier (ex: "rf_model_001.joblib")
        
        Returns:
            Path vers le fichier dans data/models
        """
        return cls.resolve("data", "models", filename)
    
    @classmethod
    def config_file(cls, filename: str = "config.yaml") -> Path:
        """
        Résout un chemin vers config.
        
        Args:
            filename: Nom du fichier (défaut: "config.yaml")
        
        Returns:
            Path vers le fichier dans config
        """
        return cls.resolve("config", filename)
    
    @classmethod
    def scripts_dir(cls) -> Path:
        """
        Résout le chemin vers scripts.
        
        Returns:
            Path vers le dossier scripts
        """
        return cls.resolve("scripts")
    
    @classmethod
    def relative_to_root(cls, path: Path) -> str:
        """
        Retourne le chemin relatif depuis la racine du projet.
        
        Args:
            path: Chemin absolu ou relatif
        
        Returns:
            Chemin relatif depuis la racine (ex: "data/source_data/microzones.pkl")
        """
        root = cls.get_project_root()
        try:
            return str(path.relative_to(root))
        except ValueError:
            # Si le chemin n'est pas sous la racine, retourner tel quel
            return str(path)


# Instance globale pour usage simple
path_resolver = PathResolver()
