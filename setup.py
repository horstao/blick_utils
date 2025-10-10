from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="blick_utils",
    version="0.1.0",
    author="Horst Erdmann",
    author_email="horstao@gmail.com",
    description="Blick Technologies Utilities Functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/blick_utils",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)