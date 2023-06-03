import setuptools

setuptools.setup(
    name='event_validation',
    version='0.5',
    author='Ronaldas Macas',
    author_email='ronaldas.macas@ligo.org',
    description='Event validation infrastructure',
    url='https://git.ligo.org/detchar/event-validation/',
    project_urls = {
        "Bug Tracker": "https://git.ligo.org/detchar/event-validation/issues"
    },
    license='MIT',
    packages=['event_validation'],
    package_data={
          'event_validation': ['templates/*'],
    },
    include_package_data=True,
    install_requires=['numpy', 'scipy', 'gwpy', 'matplotlib', 'astropy', 'pandas', 'mdutils', 'markdown-include', 'mkdocs-material-igwn', 'tabulate', 'flask', 'Flask-WTF', 'Flask-Bootstrap4', 'Flask-Table', 'gunicorn', 'python-gitlab', 'cbcflow'],
    entry_points = {
        "console_scripts": [
        'event-validation-app = event_validation.app:main',
        'event-validation-create-event = event_validation.create_event:main',
    ],
    },

)
