"""
Setup file for EDI Parser package
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_file(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

# Read version from __init__.py
version = '1.0.0'

setup(
    name='edi-parser',
    version=version,
    description='Standalone EDI parser extracted from Bots - supports EDIFACT, X12, CSV, XML, JSON and more',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='Extracted from Bots EDI Translator',
    author_email='',
    url='https://github.com/yourusername/edi-parser',
    license='GPLv3',
    packages=find_packages(exclude=['tests', 'examples']),
    include_package_data=True,
    package_data={
        'edi_parser': [
            'grammars/**/*.py',
            'grammars/**/**/*.py',
        ]
    },
    python_requires='>=3.7',
    install_requires=[
        # No external dependencies - uses only Python standard library!
    ],
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=3.0',
            'black>=22.0',
            'pylint>=2.13',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Office/Business',
        'Topic :: Communications',
    ],
    keywords='edi edifact x12 parser edi-parser trading-partner business-documents',
    project_urls={
        'Documentation': 'https://github.com/yourusername/edi-parser/blob/main/README.md',
        'Source': 'https://github.com/yourusername/edi-parser',
        'Tracker': 'https://github.com/yourusername/edi-parser/issues',
    },
)
