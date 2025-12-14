# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import sys
from PyInstaller.utils.hooks import collect_all

# Collect all cv2 data files and binaries to avoid import issues
cv2_datas, cv2_binaries, cv2_hiddenimports = collect_all('cv2')

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=cv2_binaries,
    datas=[
        ('src/resources', 'resources'),
        ('src/i18n', 'i18n'),
    ] + cv2_datas,
    hiddenimports=[
        'rawpy',
        'rawpy._rawpy',
        'numpy',
        'numpy.core',
        'numpy.core._multiarray_umath',
        'PIL',
        'PIL._imaging',
        'cv2',
        'cv2.cv2',
    ] + cv2_hiddenimports + [
        'scipy',
        'scipy.special',
        'scipy.special._ufuncs_cxx',
        'scipy.linalg',
        'scipy.linalg.cython_blas',
        'scipy.linalg.cython_lapack',
        'scipy.ndimage',
        'scipy.interpolate',
        'tifffile',
        'imageio',
        'imageio.core',
        'imageio_ffmpeg',
        'numba',
        'numba.core',
        'numba.typed',
        'yaml',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'ui',
        'ui.main_window',
        'ui.panels',
        'ui.panels.preview_panel',
        'ui.panels.file_list_panel',
        'ui.panels.parameters_panel',
        'ui.styles',
        'ui.dialogs',
        'core',
        'core.raw_processor',
        'core.stacking_engine',
        'core.exporter',
        'core.gap_filler',
        'core.image_aligner',
        'core.mask_utils',
        'core.timelapse_generator',
        'utils',
        'utils.logger',
        'utils.settings',
        'utils.file_naming',
        'i18n',
        'i18n.translator',
        'i18n.translations',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hook-cv2.py'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SuperStarTrail',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='logo.ico',  # Uncomment if you have a .ico file
)