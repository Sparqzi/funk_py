from setuptools import setup, find_packages

with open("requirements.txt", "r") as fh:
    install_requires = fh.read()

setup(
    name='funky_modifiers',
    version='0.3.2',
    description='A package containing tiny bits and bobs to remove boilerplate or just make things simpler.',
    url='https://github.com/Sparqzi/funk_py',
    author='Erich Kopp',
    license='BSD 3-Clause',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.7'
    ],
    python_requires='>3.6',
    install_requires=install_requires
)
