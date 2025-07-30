from setuptools import setup, find_packages

setup(
    name='miao',
    version='1.0',
    packages=[],
    entry_points={
        'console_scripts': [
            'miao = miao.__main__:main'
        ]
    }
)
