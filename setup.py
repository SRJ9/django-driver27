from setuptools import setup

with open('requirements.txt') as f:
     requirements = f.read().splitlines()

readme = open('README.md', 'r')
README_TEXT = readme.read()
readme.close()

setup(
    name='driver27',
    version='0.14-ALO',
    packages=['driver27', 'driver27.tests', 'driver27.migrations'],
    url='https://github.com/SRJ9/django-driver27.git',
    license='MIT',
    author='Jose ER',
    author_email='srj9es@gmail.com',
    description='Racing competition manager based on Django',
    install_requires=requirements,
    long_description = README_TEXT,
)
