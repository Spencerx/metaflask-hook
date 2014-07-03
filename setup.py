from setuptools import setup


setup(
    name='metaflask-hook',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    url='http://github.com/pocoo/metaflask-hook',
    py_modules=['metaflaskhook'],
    install_requires=[
        'Flask',
        'requests',
    ],
    description='Helps managing the metaflask repo.',
    classifiers=[
        'DO NOT UPLOAD',
    ],
)
