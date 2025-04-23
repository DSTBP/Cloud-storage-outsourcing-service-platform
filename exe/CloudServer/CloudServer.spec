# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('favicon.ico', '.'), ('utils', 'utils'), ('services', 'services'), ('business', 'business'), ('builtin_tools', 'builtin_tools'), ('favicon.ico', '.'), ('utils', 'utils'), ('services', 'services'), ('business', 'business'), ('builtin_tools', 'builtin_tools')],
    hiddenimports=[],
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
    name='CloudServer',
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
    icon=['favicon.ico'],
)
