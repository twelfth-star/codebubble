from setuptools import setup, find_packages

setup(
    name="codebubble",
    version="0.1.0",
    description="Rootless sandbox for running untrusted code",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Morris He",
    author_email="hzm20021210@gmail.com",
    url="https://github.com/twelfth-star/codebubble",
    license="MIT",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "pydantic>=1.10.0",
        "loguru>=0.6.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
)