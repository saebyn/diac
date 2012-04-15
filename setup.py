from setuptools import setup

setup(name = 'diac',
      version = '0.0.1',
      author = 'John Weaver',
      author_email = 'john@pledge4code.com',
      description = 'A compiler for a NPC dialog DSL.',
      long_description = open('README.rst').read(),
      url = 'http://github.com/saebyn/diac/',
      packages = ['diac'],
      scripts = ['bin/diac'],
      install_requires = ['pyparsing==1.5.5'],
      license = 'MIT',
      classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
      ],
)
