from setuptools import setup, find_packages

setup(
    name="pyquibbler",
    version='0.1.0',
    packages=find_packages(),
    install_requires=["matplotlib", "numpy", "magicmethods>=0.1.2,<=0.1.3"]
)
