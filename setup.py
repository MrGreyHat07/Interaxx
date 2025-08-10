from setuptools import setup, find_packages

setup(
    name="interaxx",
    version="2.0.0",
    description="Interaxx - Intelligent Header & Parameter Scanner",
    author="Deepak Rawat aka MrGreyHat07",
    author_email="",
    url="",  # Add your repo or homepage URL here if any
    packages=find_packages(),
    install_requires=[
        "playwright>=1.20.0",
        "rich",
        "pyfiglet",
    ],
    entry_points={
        'console_scripts': [
            'interaxx=interaxx:main',  # Adjust if your main script is named differently or inside a module
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
