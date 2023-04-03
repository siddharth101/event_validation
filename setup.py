import setuptools

setuptools.setup(
    name='event_validation',
    version='0.1',
    author='Ronaldas Macas',
    author_email='ronaldas.macas@ligo.org',
    description='Event validation infrastructure',
    url='https://git.ligo.org/detchar/event-validation/',
    project_urls = {
        "Bug Tracker": "https://git.ligo.org/detchar/event-validation/issues"
    },
    license='MIT',
    packages=['event_validation'],
    install_requires=['numpy', 'scipy', 'gwpy', 'matplotlib', 'astropy', 'pandas', 'mdutils', 'markdown-include', 'mkdocs-material-igwn', 'tabulate', 'flask', 'Flask-WTF', 'Flask-Bootstrap4', 'Flask-Table', 'gunicorn'],
)
