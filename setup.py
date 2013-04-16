from setuptools import setup, find_packages, Extension
import sys

sys.path.insert(0, 'dnet')
import release

setup(name='dnet',
      version=release.version,
      description='Distribution Network Evaluation Tool',
      author=release.authors[0][0],
      author_email=release.authors[0][1],
      url='https://github.com/takemaru/dnet',
      license=release.license,
      packages=['dnet'],
      requires=['graphillion', 'networkx', 'yaml'],
      test_suite='dnet.test',
      )
