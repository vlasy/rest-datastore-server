import sys
from setuptools import setup


def get_long_description():
    with open('README.md') as f:
        rv = f.read()
    return rv


def get_requirements(suffix=''):
    with open('requirements%s.txt' % suffix) as f:
        rv = f.read().splitlines()
    return rv

setup(
    name='REST-Datastore-server',
    version='1.0.0',
    url='https://github.com/vlasy/rest-datastore-server',
    license='MIT',
    author='vlasy',
    description='Simple server for REST datastore for Flask-Security',
    long_description=get_long_description(),
    install_requires=get_requirements(),
)
