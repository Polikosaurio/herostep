# herostep.spec — PyInstaller build config
# Comando: pyinstaller herostep.spec

from PyInstaller.building.build_main import Analysis, PYZ, EXE

a = Analysis(
    ['herostep.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/chars',  'assets/chars'),
        ('assets/steps',  'assets/steps'),
        ('assets/icon.ico', 'assets'),
        ('locales',       'locales'),
    ],
    hiddenimports=['pygame'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HeroStep',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # sin ventana de consola
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
