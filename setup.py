from setuptools import setup

APP = ['auto_yes.py']
DATA_FILES = [
    ('assets', [
        'assets/menubar.png',
        'assets/menubar@2x.png',
        'assets/AutoPaws.png',
    ]),
]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'assets/AutoPaws.icns',
    'plist': {
        'CFBundleName': 'Auto-Paws',
        'CFBundleDisplayName': 'Auto-Paws',
        'CFBundleIdentifier': 'io.github.ritvik-hue.autopaws',
        'CFBundleVersion': '1.0.1',
        'CFBundleShortVersionString': '1.0.1',
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
    },
    'packages': ['rumps'],
    'arch': 'arm64',
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
