from setuptools import setup, find_packages

setup(
    name='jsql',
    version='0.6',
    author='Hisham Zarka',
    author_email='hzarka@gmail.com',
    packages = find_packages(),
    package_dir = {'': '.'},
    requires = ["six"],
    install_requires = ["six"],
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

