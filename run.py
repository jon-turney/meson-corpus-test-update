#!/usr/bin/env python3

#
# Locally run meson on the list of projects
#

import argparse
import os
import sys

import corpuslib

parser = argparse.ArgumentParser('meson corpus test run tool')
parser.add_argument('--commit', help='meson commit to use', metavar='COMMIT')
parser.add_argument('--no-failfast', dest='failfast', action='store_false', help='do not stop on first failure')

args = parser.parse_args()

projects = corpuslib.fetch_project_list()

os.system('docker pull jturney/mesoncorpusci')

fail = False
for p in projects:
    if not p.branch:
        branch = 'master'
    else:
        branch = p.branch

    if not p.sourcedir:
        sourcedir = ''
    else:
        sourcedir = p.sourcedir

    cmds = ['apt-get -y update']

    if p.builddep:
        cmds.append('apt-get -y build-dep {}'.format(p.builddep))

    if p.alsoinstall:
        cmds.append('apt-get -y install {}'.format(' '.join(p.alsoinstall)))

    if args.commit:
        cmds.append('git clone https://github.com/mesonbuild/meson.git')
        # github 'pull/1234/head' references are not fetched by default
        if args.commit.startswith('pull/'):
            cmds.append('git -C meson fetch origin {}'.format(args.commit))
            cmds.append('git -C meson checkout FETCH_HEAD')
        else:
            cmds.append('git -C meson checkout {}'.format(args.commit))
        cmds.append('pip3 install ./meson')
    else:
        cmds.append('pip3 install git+https://github.com/mesonbuild/meson.git')

    if p.commit:
        cmds.append('git clone {p.repo} {p.name} && git -C {p.name} checkout {p.commit}'.format(p=p))
    else:
        cmds.append('git clone --depth=1 --branch {branch} {p.repo} {p.name}'.format(branch=branch, p=p))

    cmds.append('cd {p.name}'.format(p=p))
    if p.hacks:
        cmds.append(p.hacks)

    cmds.append('meson _build {}'.format(sourcedir))

    fail = (os.system('docker run -it --rm jturney/mesoncorpusci /bin/sh -c "%s"' % ' && '.join(cmds)) != 0) or fail

    if fail and args.failfast:
        break

sys.exit(1 if fail else 0)
