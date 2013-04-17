from setuptools import setup, find_packages, Extension
import sys

sys.path.insert(0, 'dnet')
import release

setup(name='PyDNET',
      version=release.version,
      description='Distribution Network Evaluation Tool',
      long_description="""\
DNET (Distribution Network Evaluation Tool) is an analysis tool that
works with power distribution networks for efficient and stable
operation such as loss minimization and service restoration.
""",
      author=release.authors[0][0],
      author_email=release.authors[0][1],
      url='https://github.com/takemaru/dnet',
      license=release.license,
      packages=['dnet'],
      requires=['graphillion', 'networkx', 'yaml'],
      test_suite='dnet.test',
      )
