"""Setup script for asyncio retrying."""

import re
from pathlib import Path

from setuptools import setup


def get_version():
    """从 retrying_async.py 读取版本号。"""
    path = Path(__file__).parent / 'retrying_async.py'
    content = path.read_text(encoding='utf-8')
    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
    if not match:
        raise RuntimeError("Cannot find __version__ in retrying_async.py")
    return match.group(1)


def read_readme():
    """读取 README.rst。"""
    return (Path(__file__).parent / 'README.rst').read_text(encoding='utf-8')


setup(
    name='retrying-async',
    version=get_version(),
    author='OCEAN S.A. & Timi.long',
    author_email='timilong928@gmail.com',
    url='https://github.com/lxl0928/retrying_async',
    description='Configurable retrying decorator for asyncio',
    long_description=read_readme(),
    long_description_content_type='text/x-rst',
    license='MIT',
    python_requires='>=3.7',
    install_requires=['async-timeout>=4.0.0'],
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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=['asyncio', 'retrying', 'retry', 'decorator'],
    project_urls={
        'Bug Reports': 'https://github.com/lxl0928/retrying_async/issues',
        'Source': 'https://github.com/lxl0928/retrying_async',
    },
)
