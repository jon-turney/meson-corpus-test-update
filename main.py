#!/usr/bin/env python3

import collections
import yaml

with open("template.yaml", 'r') as f:
    output = yaml.load(f)

# read list of projects from http://mesonbuild.com/Users.html
# ...

Project = collections.namedtuple('Project', ['name', 'repo', 'builddep'])

projects = []

projects.append(Project(name = 'outlier',
                        repo = 'https://github.com/kerolasa/outlier.git',
                        builddep = ['libxml2-dev']))

projects.append(Project(name = 'orc',
                        repo = 'https://anongit.freedesktop.org/git/gstreamer/orc.git',
                        builddep = []))

matrix = [{'env': ['NAME="%s"' % p.name, 'REPO=%s' % p.repo],
           'addons': { 'apt': {'packages': p.builddep + ['ninja-build'] }}} for p in projects]

output['matrix'] = {'include': matrix}

dump = yaml.dump(output, default_flow_style=False)
print(dump)
