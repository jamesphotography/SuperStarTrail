# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/resources', 'resources'),
    ],
    hiddenimports=[
        'rawpy',
        'numpy',
        'PIL',
        'cv2',
        'scipy',
        'tifffile',
        'imageio',
        'numba',
        'yaml',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'transformers',
        'tensorflow',
        'matplotlib',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SuperStarTrail',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SuperStarTrail',
)

app = BUNDLE(
    coll,
    name='SuperStarTrail.app',
    icon='logo.icns',
    bundle_identifier='com.jamesphotography.superstartrail',
    version='0.3.0',
    info_plist={
        'CFBundleName': 'SuperStarTrail',
        'CFBundleDisplayName': 'SuperStarTrail',
        'CFBundleGetInfoString': 'Star Trail Stacking Software',
        'CFBundleIdentifier': 'com.jamesphotography.superstartrail',
        'CFBundleVersion': '0.3.0',
        'CFBundleShortVersionString': '0.3.0',
        'NSHumanReadableCopyright': 'Copyright © 2024 James Photography',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
        'NSCameraUsageDescription': 'This app does not use the camera.',
        'NSPhotoLibraryUsageDescription': 'This app needs to access photos for star trail processing.',
    },
)
