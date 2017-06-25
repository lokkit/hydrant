#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'pyyaml',
    'ethjsonrpc<=99.99'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='lokkit-hydrant',
    version='0.2.0',
    description="Python service that listens on an ethereum node for incoming whisper messages.",
    long_description=readme + '\n\n' + history,
    author="Andreas Schmid",
    author_email='ikeark@gmail.com',
    url='https://github.com/lokkit/hydrant',
    packages=[
        'hydrant',
    ],
    entry_points={
        'console_scripts': [
            'hydrant = hydrant.__main__:main'
            ]
        },
    package_dir={ 'hydrant': 'hydrant' },
    include_package_data=True,
    install_requires=requirements,
    dependency_links=['https://github.com/lokkit/ethjsonrpc/archive/master.zip#egg=ethjsonrpc-99.99'],
    license="MIT license",
    zip_safe=False,
    keywords='lokkit-hydrant',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
