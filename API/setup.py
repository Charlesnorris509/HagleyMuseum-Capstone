import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="BbApi",
    version="0.1",
    author="Charles Norris",
    author_email="Charlesnorris509@gmail.com",
    description="A library set up a connection to the Blackbaud SKY API and OLTP Data Queries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Charles/BbApi-Python",
    packages=setuptools.find_packages(exclude=['resources']),
    install_requires=[
        'requests'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    python_requires=">=3.6"
)