# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import os.path
from setuptools import setup, find_packages


setup(
    name='gocept.collmex',
    version='0.2dev',
    author='gocept',
    author_email='mail@gocept.com',
    description='A Python API for Collmex import/export',
    long_description = (
        open('README.txt').read() +
        '\n\n' +
        open(os.path.join('src', 'gocept', 'collmex', 'README.txt')).read() +
        '\n\n' +
        open('CHANGES.txt').read()),
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='ZPL 2.1',
    namespace_packages=['gocept'],
    install_requires=[
        'setuptools',
        'transaction',
        'zope.interface',
        ],
    extras_require=dict(
        test=[
            'zope.testing',
            'zope.testbrowser>=3.4.3',
            ]),
)
