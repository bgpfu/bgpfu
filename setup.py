from setuptools import setup, find_packages
from codecs import open

version = open('facsimile/VERSION').read().strip()
requirements = open('facsimile/requirements.txt').read().split("\n")
test_requirements = open('facsimile/requirements-test.txt').read().split("\n")
with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='bgpfu',
    version=version,
    author='',
    author_email='',
    description='A toolbelt to assist with the automatic creation of safe prefix-filters',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
    ],
    packages=find_packages(
        include=[
            'bgpfu',
            'bgpfu.*'
        ]
    ),
    url='https://github.com/bgpfu/bgpfu',
    download_url='https://github.com/bgpfu/bgpfu/%s' % version,
    include_package_data=True,
    install_requires=requirements,
    tests_require=test_requirements,
    entry_points={
        'console_scripts': ['bgpfu=bgpfu.cli:cli']
    },
    zip_safe=True,
)
