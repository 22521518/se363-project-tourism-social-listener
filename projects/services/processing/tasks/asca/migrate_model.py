"""
One-time script to migrate the ASCA model to use correct module paths.
Run this once, then delete this script.

Usage:
    python migrate_model.py
"""
import sys
import types
import pickle
from pathlib import Path

# Paths
MODEL_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "models" / "asca"
OLD_MODEL = MODEL_DIR / "acsa.pkl"
NEW_MODEL = MODEL_DIR / "acsa_migrated.pkl"

def migrate():
    print(f"Migrating model from: {OLD_MODEL}")
    
    # Step 1: Create module aliases for loading old pickle
    if 'src' not in sys.modules:
        src_module = types.ModuleType('src')
        sys.modules['src'] = src_module
    else:
        src_module = sys.modules['src']
    
    # Import the actual modules from this project
    from projects.services.processing.tasks.asca.core import models as core_models
    from projects.services.processing.tasks.asca.core.models import components
    from projects.services.processing.tasks.asca.core import preprocessing as core_preprocessing
    
    # Create aliases so pickle can find the old paths
    sys.modules['src.models'] = core_models
    sys.modules['src.models.components'] = components
    sys.modules['src.preprocessing'] = core_preprocessing
    src_module.models = core_models
    src_module.preprocessing = core_preprocessing
    
    # Step 2: Load the old model
    with open(OLD_MODEL, 'rb') as f:
        pipeline = pickle.load(f)
    print(f"✅ Loaded model successfully")
    print(f"   Categories: {pipeline.categories}")
    print(f"   Sentiments: {pipeline.sentiments}")
    
    # Step 3: Save with new module paths (now classes are from core.models)
    with open(NEW_MODEL, 'wb') as f:
        pickle.dump(pipeline, f)
    print(f"✅ Saved migrated model to: {NEW_MODEL}")
    
    # Step 4: Rename files
    backup = MODEL_DIR / "acsa_old.pkl"
    OLD_MODEL.rename(backup)
    NEW_MODEL.rename(OLD_MODEL)
    print(f"✅ Renamed files:")
    print(f"   Old model backed up to: {backup}")
    print(f"   New model is now: {OLD_MODEL}")
    
    print("\n🎉 Migration complete! You can now remove the module aliasing code from load()")

if __name__ == "__main__":
    migrate()
