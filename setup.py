import io
import re

from setuptools import setup, find_packages

with io.open("README.md", "rt", encoding="utf8") as f:
    readme = f.read()

with io.open("src/itoko/__init__.py", "rt", encoding="utf8") as f:
    version = re.search(r"__version__ = \"(.*?)\"", f.read()).group(1)

install_requires = [
    "flask>=1.0",
    "cryptography>=2.0",
    "python-magic>=0.4",
]

setup(
    name="itoko",
    author="Alex A",
    author_email="alex@meido.ninja",
    description="Encrypted file host.",
    long_description=readme,
    version=version,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.6",
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "encrypt=itoko.cmd.encrypt:main",
            "decrypt=itoko.cmd.decrypt:main",
        ],
    }
)
