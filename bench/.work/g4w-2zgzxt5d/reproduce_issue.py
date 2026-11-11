import sys
import os

# Add /work to sys.path to import the local fnmatch
sys.path.insert(0, '/work')
import fnmatch

def test_translate_wildcards():
    try:
        # Try a simple pattern to see if it fails
        fnmatch.translate('*')
        print("Successfully translated '*'")
        fnmatch.translate('a')
        print("Successfully translated 'a'")
        fnmatch.translate('')
        print("Successfully translated ''")
    except IndexError as e:
        print(f"Caught expected IndexError: {e}")
        raise e

if __name__ == "__main__":
    try:
        test_translate_wildcards()
        print("No IndexError occurred.")
    except IndexError:
        print("IndexError occurred as expected.")
        sys.exit(1)
