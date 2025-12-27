import sys
import os
import traceback

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Python path:", sys.path)
print("CWD:", os.getcwd())
print("ENV DYLD_LIBRARY_PATH:", os.environ.get('DYLD_LIBRARY_PATH'))
print("ENV LD_LIBRARY_PATH:", os.environ.get('LD_LIBRARY_PATH'))
print("ENV PATH:", os.environ.get('PATH'))

try:
    print("\n[1] Attempting raw import lightgbm...")
    import lightgbm
    print("Successfully imported lightgbm, version:", lightgbm.__version__)
    
    print("\n[2] Attempting to create a simple Dataset to verify C++ lib loading...")
    try:
        data = [[1, 2], [3, 4]]
        label = [0, 1]
        train_data = lightgbm.Dataset(data, label=label)
        print("Successfully created lightgbm.Dataset")
    except Exception as e:
        print("Failed to create lightgbm.Dataset:", e)
        traceback.print_exc()

    print("\n[3] Attempting to import src.models.prophet_model...")
    # Add src to path if needed (though it should be implicitly added by being in root)
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        
    import src.models.prophet_model
    print("Successfully imported src.models.prophet_model")
    print("HAS_LIGHTGBM inside module:", src.models.prophet_model.HAS_LIGHTGBM)
    
except ImportError as e:
    print("Caught ImportError:")
    traceback.print_exc()
except OSError as e:
    print("Caught OSError (common for libomp issues):")
    traceback.print_exc()
except Exception as e:
    print(f"Caught generic {type(e).__name__}:")
    traceback.print_exc()
