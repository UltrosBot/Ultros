from setuptools import setup

print ""
print "*******************************"
print "This setup.py is only"
print "for use with ReadTheDocs."
print ""
print "It won't do anything useful"
print "for you - instead, do this:"
print ""
print "pip install -r requirements.txt"
print "*******************************"
print ""

setup(
    name='Ultros',
    version='1.0',
    url='http://ultos.io',
    license='',
    author='Gareth Coles',
    author_email='ultros@ultros.io',
    description='',
    install_requires=["six >= 1.6.1"]
)
