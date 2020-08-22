import setuptools

with open('README.md', 'r') as fh:
  long_description = fh.read()

setuptools.setup(
  name='jellyDatabaseConnector',
  version='0.1.0',
  author='Jimmy Johnson III',
  author_email='jay4842@gmail.com',
  description='A database connector wrapper',
  long_description=long_description,
  url='https://github.com/jay4842/jellyDatabaseConnector',
  packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)