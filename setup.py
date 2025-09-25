from setuptools import find_packages, setup

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="llmfy",
    version="0.4.1",
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
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=[
        "llm",
        "ai",
        "llm-framework",
        "llm-abstraction",
        "bedrock",
        "openai",
        "google",
    ],
    python_requires=">=3.11",
    requires=["pydantic"],
    install_requires=["pydantic"],
    extras_require={
        "openai": ["openai"],
        "boto3": ["boto3"],
        "numpy": ["numpy"],
        "faiss-cpu": ["faiss-cpu"],
    },
)
