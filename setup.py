import setuptools
from setuptools import setup

if (setuptools.__version__ != "65.5.0"):
      raise Exception

setup(
    name="climate-aware-task-scheduler",
    version="0.1.0",
    description = "Climate aware task scheduler",
    install_requires=[
          "requests_cache>=1.0",
          "PyYAML>=6.0",
    ],
    python_requires=">=3.9",
    license_files=["LICENSE"],
    entry_points={
	'console_scripts': [
	    'cats = cats:main',
	]
    },
    packages=["cats"],
)
