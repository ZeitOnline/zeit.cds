from setuptools import setup, find_packages


setup(
    name='zeit.cds',
    version='0.3.dev0',
    author='gocept, Zeit Online',
    author_email='zon-backend@zeit.de',
    url='http://www.zeit.de/',
    description="Content-Drehscheibe",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='BSD',
    namespace_packages=['zeit'],
    install_requires=[
        'setuptools',
        'gocept.filestore',
        'ftputil',
        'pyftpdlib'
    ],
    entry_points="""
        [console_scripts]
        cds-export=zeit.cds.main:export
        cds-import=zeit.cds.main:import_
        """

)
