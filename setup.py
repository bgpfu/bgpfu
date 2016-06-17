from setuptools import setup

version = open('facsimile/VERSION').read().strip()
requirements = open('facsimile/requirements.txt').read().split("\n")
test_requirements = open('facsimile/requirements-test.txt').read().split("\n")

setup(
    name='bgpfu',
    version=version,
    author='',
    author_email='',
    description='bgpfu',
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
    packages=[
        'bgpfu',
    ],
    url='https://github.com/NLNOG/bgpfu',
    download_url='https://github.com/NLNOG/bgpfu/%s' % version,
    include_package_data=True,
    install_requires=requirements,
    test_requires=test_requirements,
    entry_points='''
        [console_scripts]
        bgpfu=bgpfu.cli:cli
    ''',
    zip_safe=True,
)

