from setuptools import setup

setup(
    name='console_interface',
    version='0.1.0',
    description='MARS circular track system control',
    py_modules=['console_interface'],
    install_requires=[
        'Click', 
        'pyvisa',
        'numpy',
        'pyserial',
        'nidaqmx'
    ],
    entry_points={
        'console_scripts': [
            'ctrack = console_interface:cli',
        ],
    },
)