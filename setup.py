from setuptools import setup, find_packages

setup(
    name="palantir",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest>=8.0.0",
        "pytest-asyncio>=1.0.0",
        "pytest-cov>=6.0.0",
        "aiohttp>=3.9.0",
        "pyyaml>=6.0.0",
        "fastapi>=0.109.0",
        "passlib>=1.7.4",
        "python-jose[cryptography]>=3.3.0",
        "python-multipart>=0.0.9",
        "sqlalchemy>=2.0.0",
        "aiosqlite>=0.20.0",
        "gitpython>=3.1.40"
    ],
    python_requires=">=3.8"
) 