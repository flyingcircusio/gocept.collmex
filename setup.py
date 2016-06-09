import os.path
from setuptools import setup, find_packages


setup(
    name='gocept.collmex',
    version='1.8.1',
    author='gocept',
    author_email='mail@gocept.com',
    description='Python-bindings for the Collmex import/export API',
    url='http://pypi.python.org/pypi/gocept.collmex',
    classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Environment :: Plugins',
      'Intended Audience :: Developers',
      'License :: OSI Approved',
      'License :: OSI Approved :: Zope Public License',
      'Operating System :: OS Independent',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.3',
      'Programming Language :: Python :: 3.4',
    ],
    long_description = (
        open('README.txt').read() +
        '\n\n' +
        open(os.path.join('src', 'gocept', 'collmex', 'doctest.txt')).read() +
        '\n\n' +
        open('CHANGES.txt').read()),
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='ZPL 2.1',
    namespace_packages=['gocept'],
    install_requires=[
        'gocept.cache >= 0.6.1',
        'setuptools >= 1.0',
        'transaction >= 1.4',
        'zope.deprecation >= 4.0',
        'zope.interface >= 4.0',
        'webtest >= 2.0',
        'wsgiproxy2',
        'six'
        ],
    extras_require=dict(
        test=[
            'zope.testing >= 4.0',
            'mock >= 1.0',
            ]),
)
