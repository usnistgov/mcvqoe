#!/usr/bin/env python
import setuptools

with open("README.md", "r",encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="mcvqoe",
    author="PSCR",
    author_email="PSCR@PSCR.gov",
    description="Graphical interface for mcvqoe measurements",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.nist.gov/gitlab/PSCR/MCV/mcv-qoe-gui",
    packages=setuptools.find_namespace_packages(include=['mcvqoe.*']),
    include_package_data=True,
    use_scm_version={'write_to' : 'mcvqoe/hub/version.py'},
    setup_requires=['setuptools_scm'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ],
    license='NIST software License',
    install_requires=[
        'abcmrt16',
        'mcvqoe-base',
        'mcvqoe-psud',
        'mcvqoe-intelligibility',
        'mcvqoe-accesstime',
        'mcvqoe-mouth2ear',
        'numpy',
        'pandas',
        'dash',
        'flask',
        'plotly',
        'requests',
    ],
    extras_require={
        'plots': ['PyQt5'],
    },
    entry_points={
        'gui_scripts':[
            'mcvqoe=mcvqoe.hub.mcv_qoe_gui:main',
        ],
        'console_scripts':[
            'mcvqoe-eval=mcvqoe.hub.eval_index:main',
            ]
    },
    python_requires='>=3.8',
)

