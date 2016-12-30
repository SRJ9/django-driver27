from setuptools import setup, find_packages

with open('requirements.txt') as f:
     requirements = f.read().splitlines()

readme = open('README.rst', 'r')
README_TEXT = readme.read()
readme.close()

setup(
    name='django-driver27',
    version='0.19.2.1',
    include_package_data=True,
    packages=find_packages(),
    url='https://github.com/SRJ9/django-driver27.git',
    download_url='https://github.com/SRJ9/django-driver27/archive/master.zip',
    license='MIT',
    author='Jose ER',
    author_email='srj9es@gmail.com',
    description='Racing competition manager based on Django',
    install_requires=requirements,
    long_description=README_TEXT,
    keywords=['Django', 'motorsport', 'formula one', 'formula 1', 'f1', 'manager'],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stablegit
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        #
        # # Specify the Python versions you support here. In particular, ensure
        # # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ]

)
