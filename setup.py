from setuptools import setup

setup(
    name="teo-engine",
    version="1.0.0",
    author="EcoCode Solutions",
    author_email="info@ecocodesolution.com",
    description="Trinity Energy Optimizer (TEO) — Homeostatic computing for balanced performance, power, and thermal load.",
    long_description=open("README.md", encoding="utf-8").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/EcoCodeSolutions/TEO",
    py_modules=["teo_cli"],
    include_package_data=True,
    install_requires=[
        "psutil>=5.9.0",
        "click>=8.0.0",
        "py-cpuinfo>=9.0.0",
    ],
    entry_points={
        "console_scripts": [
            "teo=teo_cli:main",
        ],
    },
    python_requires=">=3.10",
)
