from setuptools import setup, find_packages


setup(
    name='funky_modifiers',
    version='0.1.2',
    description='A package containing tiny bits and bobs to remove boilerplate or just make things simpler.',
    url='https://github.com/Sparqzi/funk_py',
    author='Erich Kopp',
    license='BSD 3-Clause',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    classifiers=[
        'Development Status :: 1 - Planning',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.10'
    ]
)
