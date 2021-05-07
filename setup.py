from setuptools import setup


setup(
    name='samlwebcookie',
    version='1.0.0',
    author='Christopher Thorne',
    url='https://cthorne.me',
    install_requires=[
        'bs4',
        'requests',
        'requests-ntlm',
    ],
    packages=['.'],
    entry_points={
        'console_scripts': [
            'samlwebcookie=webcookie:main',
        ]
    },
)
