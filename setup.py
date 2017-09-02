from setuptools import setup, find_packages

setup(
    name='jsql',
    version='0.1',
    author='Hisham Zarka',
    author_email='hzarka@gmail.com',
    packages = find_packages(),
    package_dir = {'': '.'},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    zip_safe=True,
)

