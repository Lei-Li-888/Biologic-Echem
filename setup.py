from setuptools import setup, find_packages

setup(
    name="biologic_echem",
    version="0.1.0",
    description="Plotting and analysis toolkit for BioLogic potentiostat data",
    author="Lei Li",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24",
        "pandas>=2.0",
        "matplotlib>=3.7",
        "openpyxl>=3.1",
        "scipy>=1.10",
    ],
    extras_require={
        "mpr": ["galvani>=0.2"],
    },
)
