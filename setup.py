from setuptools import find_packages
from setuptools import setup
import os.path


setup(
    name='gocept.collmex',
    version='2.1.0',
    author='gocept',
    author_email='mail@gocept.com',
    description='Python-bindings for the Collmex import/export API',
    url='https://github.com/gocept/gocept.collmex',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved',
        'License :: OSI Approved :: Zope Public License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    long_description=(
        open('README.rst').read() +
        '\n\n' +
        open(os.path.join('src', 'gocept', 'collmex', 'doctest.rst')).read() +
        '\n\n' +
        open('CHANGES.rst').read()),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='ZPL 2.1',
    namespace_packages=['gocept'],
    python_requires='>=3.7',
    install_requires=[
        'gocept.cache >= 0.6.1',
        'setuptools >= 1.0',
        'transaction >= 1.4',
        'zope.deprecation >= 4.0',
        'zope.interface >= 4.0',
        'webtest >= 2.0',
        'wsgiproxy2',
    ],
    extras_require=dict(
        test=[
            'zope.testing >= 4.0',
            'mock >= 1.0',
        ]),
)
