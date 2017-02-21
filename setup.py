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
      classifiers=[ # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
        ],
      keywords=['power distribution network', 'optimization', 'graph'],
      author=release.authors[0][0],
      author_email=release.authors[0][1],
      url='https://github.com/takemaru/dnet',
      license=release.license,
      packages=['dnet'],
      install_requires=['graphillion', 'networkx', 'pyyaml'],
      test_suite='dnet.test',
      )
