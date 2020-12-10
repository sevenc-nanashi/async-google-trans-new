import setuptools

with open("README.md", "r", encoding='utf-8') as f:
     long_desc = f.read()
setuptools.setup(
    name="async_google_trans_new",
    version="1.0.0",
    author="sevenc_nanashi",
    description="google_trans_new but it is async!",
    long_description=long_desc,
    long_description_content_type='text/markdown',
    url="https://github.com/sevenc-nanashi/async_google_trans_new",
    packages=setuptools.find_packages(),
    
    classifiers=[
        "Programming Language :: Python :: 3.8.3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)