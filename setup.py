from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pysberbps',
    version='0.0.1.dev1',

    description='Wrapper over Sberbank Acquiring API',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/mnach/pysberbank',

    # Author details
    author='Mikhail Nacharov',
    author_email='mnach@ya.ru',

    # Choose your license
    license='BSD License',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='acquiring sberbank bps processing E-Retail',
    packages=find_packages(),
    install_requires=[],
    extras_require={
        'soap': ['suds-py3k']
    }
)
