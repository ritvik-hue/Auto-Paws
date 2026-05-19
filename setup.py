from setuptools import setup

APP = ['auto_yes.py']
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'Auto-Paws',
        'CFBundleDisplayName': 'Auto-Paws',
        'CFBundleIdentifier': 'io.github.ritvik-hue.autopaws',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
    },
    'packages': ['rumps'],
    'arch': 'arm64',
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
