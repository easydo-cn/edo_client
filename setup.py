#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
requires = [
    'py-oauth2>=0.0.10', 'requests', 'certifi', 'paho-mqtt',
    # Aliyun
    'oss2==2.5.0',
    'cryptography==3.2.1',
    'aliyun-python-sdk-core>=2.13.34',
]

kw = dict(
    name='edo_client',
    version='6.3.3',
    description='SDK for easydo.cn',
    long_description=README,
    author='Easydo team',
    author_email='code@easydo.cn',
    url='https://github.com/everydo/python-sdk',
    download_url='https://github.com/everydo/python-sdk',
    packages=find_packages(),
    install_requires=requires,
    tests_require=requires,
    test_suite='tests',
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={
        'console_scripts': [
            'edo_upload = scripts.batch_upload:main',
        ]
    })

setup(**kw)
