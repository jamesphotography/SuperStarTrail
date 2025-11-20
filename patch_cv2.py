#!/usr/bin/env python3
"""
Patch cv2's __init__.py to remove recursion detection for PyInstaller compatibility
"""
import shutil
from pathlib import Path

# Find cv2's __init__.py
cv2_init = Path(".venv/lib/python3.12/site-packages/cv2/__init__.py")

if not cv2_init.exists():
    print(f"❌ cv2 __init__.py not found at {cv2_init}")
    exit(1)

# Backup original
backup = cv2_init.with_suffix('.py.backup')
if not backup.exists():
    shutil.copy(cv2_init, backup)
    print(f"✓ Created backup: {backup}")

# Read original
content = cv2_init.read_text()

# Remove the recursion check (lines 74-76)
# Replace the problematic code with a pass
original_check = """    if hasattr(sys, 'OpenCV_LOADER'):
        print(sys.path)
        raise ImportError('ERROR: recursion is detected during loading of "cv2" binary extensions. Check OpenCV installation.')
    sys.OpenCV_LOADER = True"""

patched_check = """    # Recursion check disabled for PyInstaller compatibility
    # if hasattr(sys, 'OpenCV_LOADER'):
    #     print(sys.path)
    #     raise ImportError('ERROR: recursion is detected during loading of "cv2" binary extensions. Check OpenCV installation.')
    sys.OpenCV_LOADER = True"""

if original_check in content:
    content = content.replace(original_check, patched_check)
    cv2_init.write_text(content)
    print("✓ Patched cv2/__init__.py - recursion check disabled")
else:
    print("⚠️  Recursion check code not found or already patched")

print("\nTo restore original:")
print(f"  cp {backup} {cv2_init}")
