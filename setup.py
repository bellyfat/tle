#!/usr/bin/python
from setuptools import setup, find_packages
import os

EXTRAS_REQUIRES = dict(
    web=[
        'requests>=0.14.1',
    ],
    test=[
        'pytest>=2.2.4',
        'mock>=0.8.0',
        ],
    dev=[
        'ipython>=0.13',
        ],
    )

# Pypi package documentation
root = os.path.dirname(__file__)
path = os.path.join(root, 'README.rst')
with open(path) as fp:
    long_description = fp.read()

# Tests always depend on all other requirements, except dev
for k,v in EXTRAS_REQUIRES.iteritems():
    if k == 'test' or k == 'dev':
        continue
    EXTRAS_REQUIRES['test'] += v

setup(
    name='tle',
    version='0.0.1',
    description='Services and tools for The Lean Entrepreneur',
    long_description=long_description,
    author='Andres Buritica',
    author_email='andres@thelinuxkid.com',
    maintainer='Andres Buritica',
    maintainer_email='andres@thelinuxkid.com',
    # url='https://github.com/thelinuxkid/tle',
    license='MIT',
    packages = find_packages(),
    test_suite='nose.collector',
    install_requires=[
        'setuptools',
        ],
    extras_require=EXTRAS_REQUIRES,
    entry_points={
        'console_scripts': [
            'email-forward = tle.cli.email_forward:main[web]',
            ],
        },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    ],
)
