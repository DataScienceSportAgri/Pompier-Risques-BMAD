"""
Tests unitaires pour pickle_utils (format standardisé).
Story 2.1.4 - Système centralisé de résolution de chemins
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.core.utils.pickle_utils import (
    PICKLE_FORMAT_VERSION,
    create_pickle_data,
    get_pickle_metadata,
    load_pickle,
    save_pickle,
)


class TestCreatePickleData:
    """Tests pour create_pickle_data."""
    
    def test_create_basic_structure(self):
        """Test création structure de base."""
        data = {"key": "value"}
        pickle_data = create_pickle_data(
            data=data,
            data_type="test",
            description="Test data"
        )
        
        assert 'data' in pickle_data
        assert 'metadata' in pickle_data
        assert pickle_data['data'] == data
        assert pickle_data['metadata']['type'] == "test"
        assert pickle_data['metadata']['description'] == "Test data"
        assert pickle_data['metadata']['version'] == PICKLE_FORMAT_VERSION
        assert isinstance(pickle_data['metadata']['created_at'], datetime)
    
    def test_create_with_run_id(self):
        """Test création avec run_id."""
        pickle_data = create_pickle_data(
            data={},
            data_type="vectors",
            description="Test",
            run_id="001"
        )
        
        assert pickle_data['metadata']['run_id'] == "001"
    
    def test_create_with_schema_version(self):
        """Test création avec schema_version."""
        pickle_data = create_pickle_data(
            data={},
            data_type="vectors",
            description="Test",
            schema_version="1.0"
        )
        
        assert pickle_data['metadata']['schema_version'] == "1.0"
    
    def test_create_with_extra_metadata(self):
        """Test création avec métadonnées supplémentaires."""
        pickle_data = create_pickle_data(
            data={},
            data_type="test",
            description="Test",
            custom_field="custom_value",
            another_field=42
        )
        
        assert pickle_data['metadata']['custom_field'] == "custom_value"
        assert pickle_data['metadata']['another_field'] == 42


class TestSaveLoadPickle:
    """Tests pour save_pickle et load_pickle."""
    
    def test_save_and_load_basic(self):
        """Test sauvegarde et chargement de base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.pkl"
            
            test_data = {"key": "value", "number": 42}
            
            save_pickle(
                data=test_data,
                path=path,
                data_type="test",
                description="Test data"
            )
            
            assert path.exists()
            
            loaded_data = load_pickle(path)
            
            assert loaded_data == test_data
    
    def test_save_and_load_with_validation(self):
        """Test sauvegarde et chargement avec validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.pkl"
            
            test_data = {"vectors": []}
            
            save_pickle(
                data=test_data,
                path=path,
                data_type="vectors",
                description="Vectors test",
                run_id="001"
            )
            
            # Chargement avec validation
            loaded_data = load_pickle(
                path=path,
                expected_type="vectors",
                expected_version=PICKLE_FORMAT_VERSION
            )
            
            assert loaded_data == test_data
    
    def test_load_wrong_type_raises_error(self):
        """Test que chargement avec mauvais type lève une erreur."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.pkl"
            
            save_pickle(
                data={},
                path=path,
                data_type="vectors",
                description="Test"
            )
            
            with pytest.raises(ValueError, match="Type de données inattendu"):
                load_pickle(path, expected_type="events")
    
    def test_load_wrong_version_raises_error(self):
        """Test que chargement avec mauvaise version lève une erreur."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.pkl"
            
            save_pickle(
                data={},
                path=path,
                data_type="test",
                description="Test"
            )
            
            with pytest.raises(ValueError, match="Version du format inattendue"):
                load_pickle(path, expected_version="2.0")
    
    def test_load_non_standardized_raises_error(self):
        """Test que chargement d'un pickle non standardisé lève une erreur."""
        import pickle
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.pkl"
            
            # Sauvegarder un pickle non standardisé
            with open(path, 'wb') as f:
                pickle.dump({"not": "standardized"}, f)
            
            with pytest.raises(ValueError, match="Format pickle non standardisé"):
                load_pickle(path)
    
    def test_save_creates_parent_dirs(self):
        """Test que save_pickle crée les dossiers parents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "nested" / "test.pkl"
            
            save_pickle(
                data={},
                path=path,
                data_type="test",
                description="Test"
            )
            
            assert path.exists()
            assert path.parent.exists()


class TestGetPickleMetadata:
    """Tests pour get_pickle_metadata."""
    
    def test_get_metadata(self):
        """Test récupération des métadonnées."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.pkl"
            
            save_pickle(
                data={"test": "data"},
                path=path,
                data_type="test",
                description="Test description",
                run_id="001"
            )
            
            metadata = get_pickle_metadata(path)
            
            assert metadata['type'] == "test"
            assert metadata['description'] == "Test description"
            assert metadata['version'] == PICKLE_FORMAT_VERSION
            assert metadata['run_id'] == "001"
            assert isinstance(metadata['created_at'], datetime)
    
    def test_get_metadata_non_standardized_raises_error(self):
        """Test que récupération métadonnées d'un pickle non standardisé lève une erreur."""
        import pickle
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.pkl"
            
            # Sauvegarder un pickle non standardisé
            with open(path, 'wb') as f:
                pickle.dump({"not": "standardized"}, f)
            
            with pytest.raises(ValueError, match="Format pickle non standardisé"):
                get_pickle_metadata(path)


class TestPickleFormatCompliance:
    """Tests pour vérifier la conformité au format standardisé."""
    
    def test_format_structure(self):
        """Test que la structure respecte le format standardisé."""
        pickle_data = create_pickle_data(
            data={"test": "data"},
            data_type="test",
            description="Test"
        )
        
        # Vérifier structure
        assert isinstance(pickle_data, dict)
        assert 'data' in pickle_data
        assert 'metadata' in pickle_data
        
        metadata = pickle_data['metadata']
        assert 'version' in metadata
        assert 'created_at' in metadata
        assert 'type' in metadata
        assert 'description' in metadata
    
    def test_metadata_required_fields(self):
        """Test que tous les champs obligatoires sont présents."""
        pickle_data = create_pickle_data(
            data={},
            data_type="test",
            description="Test"
        )
        
        metadata = pickle_data['metadata']
        required_fields = ['version', 'created_at', 'type', 'description']
        
        for field in required_fields:
            assert field in metadata, f"Champ obligatoire manquant: {field}"
    
    def test_version_consistency(self):
        """Test que la version est cohérente."""
        pickle_data = create_pickle_data(
            data={},
            data_type="test",
            description="Test"
        )
        
        assert pickle_data['metadata']['version'] == PICKLE_FORMAT_VERSION
