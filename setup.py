"""Basic seup for entry points."""
from setuptools import setup

setup(name='flt',
      version='0.1',
      description='A simple tool to label faces.',
      author='Dave Greenwood',
      py_modules=["flt"],
      zip_safe=False,
      entry_points={'console_scripts': [
          "flt=flt.flt:main",]}
      )
