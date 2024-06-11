from setuptools import setup

setup(
    name='AB-Connect',
    version='3.1.8',
    description='This app provides Allen-Bradley PLC tags as datalayer nodes',
    author='alex4acre, S-Gilk',
    setup_requires = ['wheel'],
    install_requires = ['ctrlx-datalayer', 'pylogix', 'pycomm3'],    
    packages=['app', 'helper'],
    # https://stackoverflow.com/questions/1612733/including-non-python-files-with-setup-py
    package_data={'./': []},
    scripts=['main.py'],
    license='Copyright (c) 2020-2022 Bosch Rexroth AG, Licensed under MIT License'
)
