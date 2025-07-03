# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main_app.py'],
    pathex=['.'],  # Add current folder so local modules are found
    binaries=[],
    datas=[
        ('assets', 'assets'),   # your assets folder
        ('tools', 'tools'),     # your tools folder
        ('license_gate.py', '.'), # include license_gate.py
        ('utils.py', '.'),         # include utils.py
    ],
    hiddenimports=['license_gate', 'utils'],  # explicitly add as hidden imports
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main_app',
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
    icon=['assets\\LOGO.ico'],
)
