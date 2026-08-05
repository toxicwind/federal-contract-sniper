from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="federal-contract-sniper",
    version="4.0.0",
    author="Christopher Ortega",
    author_email="denverchrisortega@gmail.com",
    description="Autonomous federal contracting intelligence — SAM.gov OSINT, ICF reverse engineering, 80234 geo-scoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/toxicwind/federal-contract-sniper",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.28.0",
        "pandas>=1.5.0",
        "numpy>=1.23.0",
        "scikit-learn>=1.2.0",
        "matplotlib>=3.6.0",
    ],
    entry_points={
        "console_scripts": [
            "federal-sniper=federal_sniper.cli:main",
        ],
    },
)
