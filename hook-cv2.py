"""
Runtime hook for cv2 to fix recursion detection issue in PyInstaller

OpenCV checks for sys.OpenCV_LOADER attribute to detect recursion.
In PyInstaller bundles, this check triggers incorrectly.
We need to delete this attribute if it exists before cv2 loads.
"""
import sys

# CRITICAL FIX: Remove OpenCV_LOADER attribute that triggers false recursion detection
# This must happen BEFORE cv2 imports
if hasattr(sys, 'OpenCV_LOADER'):
    delattr(sys, 'OpenCV_LOADER')
