from setuptools import find_packages, setup

setup(
    name='kraken_ore_generator',
    version='0.0.1',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    description='Kraken Ore Generator',
    entry_points={
        'console_scripts': ['kraken_ore_generator=kraken_ore_generator.cli:cli'],
    },
    install_requires=['cdm-metadata-client', 'sortedcollections', 'requests', 'tqdm', 'click', 'msgpack', 'pandas'],
)
