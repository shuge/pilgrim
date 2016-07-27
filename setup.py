try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='pilgrim',
    version='201512',
    packages=['pilgrim', 'pilgrim.codecs', 'pilgrim.decoders'],
    url='https://github.com/shuge/pilgrim',
    license='The BSD 3-Clause License',
    author='Shuge Lee',
    author_email='shuge.lee@gmail.com',
    description='A Python Imaging Library extensions for dds, blp, ftex and ico image format processing.',

    scripts=[
        'scripts/pilgrim_convert.py',
        'scripts/pilgrim_show.py',
    ],

    requires=[
        'pillow',
        'helper_string',
    ],
)
