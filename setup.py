from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="llmfy",
    version="0.2.1",
    packages=find_packages(),
    include_package_data=True,
    description="`LLMfy` is a framework for developing applications with large language models (LLMs).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="irufano",
    author_email="irufano.official@gmail.com",
    url="https://github.com/irufano/llmfy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    requires=["pydantic"],
    install_requires=["pydantic"],
    extras_require={
        "openai": ["openai"],
        "boto3": ["boto3"],
    },
)
