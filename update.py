#!/usr/bin/env python3

#
# Construct a .travis.yml to run the git master of meson on the list of projects
#

import argparse
import os
import sys
import yaml

import corpuslib

#
# argument parsing
#

parser = argparse.ArgumentParser('meson corpus test updater tool')
parser.add_argument('conf', help='configuration file', metavar='CONFFILE')
parser.add_argument('yml', help='.travis.yml output file', metavar='TRAVISFILE')
parser.add_argument('commit', help='meson commit to use', metavar='COMMIT', nargs='?')
parser.add_argument('--build', dest='build', action='store_true', help='build as well as generate')

args = parser.parse_args()

#
# build projects list
#

projects = corpuslib.fetch_project_list()

#
# read template.yml and insert project list into build matrix
#

scriptdir = os.path.dirname(os.path.realpath(sys.argv[0]))
with open(os.path.join(scriptdir, "template.yaml")) as f:
    output = yaml.load(f)

matrix = [{'env': ['NAME=%s' % p.name, 'REPO=%s' % p.repo]
                   + (['MESON_COMMIT=%s' % args.commit] if args.commit else [])
                   + (['BRANCH=%s' % p.branch] if p.branch else [])
                   + (['COMMIT=%s' % p.commit] if p.commit else [])
                   + (['BUILDDEP=%s' % p.builddep] if p.builddep else [])
                   + (['ALSOINSTALL="%s"' % ' '.join(p.alsoinstall)] if p.alsoinstall else [])
                   + (['SOURCEDIR=%s' % p.sourcedir] if p.sourcedir else [])
                   + (['BUILD=yes'] if args.build else [])
                   + (['HACKS=%s' % corpuslib.shell_protect(p.hacks)] if p.hacks else [])} for p in projects]

output['matrix'] = {'include': matrix}

with open(args.yml, 'w') as f:
    print(yaml.dump(output, default_flow_style=False, width=128), file=f)
