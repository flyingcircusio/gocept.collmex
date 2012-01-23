# Copyright (c) 2008 gocept gmbh & co. kg
# See also LICENSE.txt

import os.path
from setuptools import setup, find_packages


setup(
    name='gocept.collmex',
    version='1.0',
    author='gocept',
    author_email='mail@gocept.com',
    description='Python-bindings for the Collmex import/export API',
    classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Environment :: Plugins',
      'Intended Audience :: Developers',
      'License :: OSI Approved',
      'License :: OSI Approved :: Zope Public License',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 2 :: Only',
    ],
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
        'gocept.cache>=0.3',
        'setuptools',
        'transaction',
        'zope.deprecation',
        'zope.interface',
        'zope.testbrowser>=3.4.3',
        ],
    extras_require=dict(
        test=[
            'zope.testing',
            'mock',
            ]),
)
