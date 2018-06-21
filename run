#!/usr/bin/env python3

#
# Locally run meson on the list of projects
#

import argparse
import os
import shlex
import sys

import corpuslib

parser = argparse.ArgumentParser('meson corpus test run tool')
parser.add_argument('--commit', help='meson commit to use', metavar='COMMIT')
parser.add_argument('--no-failfast', dest='failfast', action='store_false', help='do not stop on first failure')
parser.add_argument('--interactive', dest='interactive', action='store_true', help='run an interactive shell after failure')
parser.add_argument('--build', dest='build', action='store_true', help='build as well as generate')
parser.add_argument('project', help='projects to test', metavar='PROJECT', nargs='*')

args = parser.parse_args()

projects = corpuslib.fetch_project_list()

unknown = set.difference(set(args.project), set([p.name for p in projects]))
if unknown:
    print('unknown projects: %s' % ', '.join(sorted(unknown)))
    sys.exit(1)

os.system('docker pull jturney/mesoncorpusci')

fail = False
for p in projects:
    if args.project and p.name not in args.project:
        continue

    if not p.branch:
        branch = 'master'
    else:
        branch = p.branch

    if not p.sourcedir:
        sourcedir = ''
    else:
        sourcedir = p.sourcedir

    cmds = []

    if os.path.exists('/etc/apt/apt.conf.d/01proxy'):
        with open('/etc/apt/apt.conf.d/01proxy') as f:
            proxy = f.read()
        cmds.append('echo {} >/etc/apt/apt.conf.d/01proxy'.format(shlex.quote(proxy)))

    cmds.append('chronic apt-get -y update')

    if p.builddep:
        cmds.append('chronic apt-get -y build-dep {}'.format(p.builddep))

    if p.alsoinstall:
        cmds.append('chronic apt-get -y install {}'.format(' '.join(p.alsoinstall)))

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

    if args.build:
        cmds.append('DESTDIR=/install ninja -C _build all test install')

    cmd = ' &&\n'.join(cmds)
    if args.interactive:
        cmd += ' || bash'

    with open('script', 'w') as f:
        print(cmd, file=f)

    fail = (os.system('docker run -it --rm jturney/mesoncorpusci /bin/sh -c "$(cat script)"') != 0) or fail

    if fail and args.failfast:
        break

sys.exit(1 if fail else 0)
