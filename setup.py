import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="TimePlotGui", # Replace with your own username
    version="0.0.9",
    author="Christopher Milne and Kevin Hauser",
    author_email="camilne9@gmail.com",
    description="GUI for real time data visualization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kehaus/time-plot-gui",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
