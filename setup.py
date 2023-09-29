from setuptools import find_namespace_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='amorphous_fortress',
      version='0.0.1',
      author="NYU Game Innovation Lab",
      author_email="mlc761@nyu.edu",
      description="Amorphous Fortress",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/dipikarajesh18/duck-fortress",
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
      ],
      packages=find_namespace_packages(include=["hydra_plugins.*"]),
      scripts=[
      ],
)
