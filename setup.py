from setuptools import setup, find_packages

setup(
    name='miao',
    version='1.02',
    packages=[],
    entry_points={
        'console_scripts': [
            'miao = miao.__main__:main'
        ]
    }
)
