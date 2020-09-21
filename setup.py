import io
import os
import re

from setuptools import setup


def get_version():
    regex = r"__version__\s=\s\'(?P<version>[\d\.]+?)\'"

    path = ('retrying_async.py',)

    return re.search(regex, read(*path)).group('version')


def read(*parts):
    filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts)

    with io.open(filename, encoding='utf-8', mode='rt') as fp:
        return fp.read()


setup(
    name='retrying-async',
    version=get_version(),
    author='OCEAN S.A. & Timi.long',
    author_email='lixiaolong@smuer.cn',
    url='https://github.com/lxl0928/retrying_async',
    description='Simple retrying for asyncio',
    long_description=read('README.rst'),
    install_requires=['async_timeout'],
    extras_require={},
    py_modules=['retrying_async'],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords=['asyncio', 'retrying'],
)
