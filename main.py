#!/usr/bin/env python3

#
# Construct a .travis.yml to run the git master of meson on the list of projects
#

import argparse
import collections
import os
import re
import string
import sys
import urllib.request
import yaml

#
# argument parsing
#

parser = argparse.ArgumentParser('meson corupus test updater tool')
parser.add_argument('yml', help='.travis.yml file', metavar='YMLFILE')
parser.add_argument('docker', help='Dockerfile', metavar='DOCKERFILE')
args = parser.parse_args()

#
# static data
#

Project = collections.namedtuple('Project', ['name', 'repo', 'branch', 'builddep', 'sourcedir', 'hacks'])

# map project names to source package names
namemap = {
    'gstreamer': 'gstreamer1.0',
    'libfuse' : 'fuse',
    'zstandard': 'zstd',
}

# build dependencies to use instead of, or as well (if first is '+'), the builddeps from package manager
builddep = {
    'budgie_desktop': ['valac', 'libgtk-3-dev'],
    'dpdk': [],
    'hardcode-tray': ['libgirepository1.0-dev', 'libgtk-3-dev'],
    'jsoncpp': [],
    'hexchat': ['+', 'libluajit-5.1-dev'],
    'libfuse': ['+', 'udev'],
    'libhttpseverywhere': ['valac', 'libjson-glib-dev', 'libsoup2.4-dev', 'libgee-0.8-dev', 'libarchive-dev', 'gobject-introspection'],
    'libosmscout': [],
    'outlier': [],
    'parzip': [],
    'szl': [],
    'valum': ['valac', 'libsoup2.4-dev'],
}

# map urls to git repo urls
url_remap = {
    'http://dpdk.org/ml/archives/dev/2018-January/089724.html': 'git://dpdk.org/dpdk',
    'https://www.frida.re/': 'https://github.com/frida/frida.git',
    'https://wiki.gnome.org/Apps/Geary': 'https://git.gnome.org/browse/geary',
    'https://ebassi.github.io/graphene/': 'git://github.com/ebassi/graphene',
    'https://mail.gnome.org/archives/grilo-list/2017-February/msg00000.html': 'https://git.gnome.org/browse/grilo',
    'https://git.gnome.org/browse/grilo-plugins/commit/?id=ea047c4fb63e90268eb795ed91a09a2be5068a4c': 'https://git.gnome.org/browse/grilo-plugins',
    'https://github.com/grindhold/libhttpseverywhere': 'https://git.gnome.org/browse/libhttpseverywhere',  # moved
    'https://www.mesa3d.org/': 'git://anongit.freedesktop.org/mesa/mesa',
    'https://git.gnome.org/browse/nautilus/commit/?id=ed5652c89ac0654df2e82b54b00b27d51c825465': 'https://gitlab.gnome.org/GNOME/nautilus.git',
    'https://pipewire.org/': 'https://github.com/PipeWire/pipewire.git',
    'http://pitivi.org/': 'https://git.gnome.org/browse/pitivi',
    'https://wiki.gnome.org/Apps/Sysprof': 'git://git.gnome.org/sysprof',
    'https://taisei-project.org/': 'https://github.com/taisei-project/taisei.git',
    'https://lists.freedesktop.org/archives/wayland-devel/2016-November/031984.html': 'git://anongit.freedesktop.org/wayland/libinput', # not merged yet...
    'https://github.com/facebook/zstd/commit/4dca56ed832c6a88108a2484a8f8ff63d8d76d91': 'https://github.com/facebook/zstd.git'
}

# blacklist of projects we don't attempt to build
blacklist = [
    'arduino_sample_project',  # work out how to setup cross-env
    'frida', # no meson.build ?!?
]

# broken by PR #3035
blacklist += [
    'dbus-broker',
    'gnome_recipes',
    'nautilus',
]

# if we don't want to checkout master, use a branch, tag or hash
branch_overrides = {
    'lightdm-webkit2-greeter': 'stable',
}

# if meson.build is not in the root of the source checkout
sourcedir = {
    'zstandard': 'contrib/meson',
}

# misc hacks needed to build
hacks = {
    'szl': 'git submodule update --init',  # uses submodules, but not as subprojects
}

#
# fetch project list, extract projects
#

project_list_url = "https://raw.githubusercontent.com/mesonbuild/meson/master/docs/markdown/Users.md"
content = urllib.request.urlopen(project_list_url).read().decode()

projects = []
for l in content.splitlines():
    if l.startswith(' - '):
        matches = re.finditer(r'\[(.*?)\]\((.*?)\)', l)
        for m in matches:
            name = m.group(1)
            url = m.group(2)

            name = name.lower().replace(' ','_')

            if name in blacklist:
                continue

            url = url_remap.get(url, url)

            # workaround freedesktop.org CA not in trusty (?)
            url = re.sub(r'http(s|)://cgit.freedesktop.org/', r'git://anongit.freedesktop.org/', url)

            projects.append(Project(name = name,
                                    repo = url,
                                    builddep = builddep.get(name, []),
                                    branch = branch_overrides.get(name, 'master'),
                                    sourcedir = sourcedir.get(name, None),
                                    hacks = hacks.get(name, None)))


#
# read Dockerfile.template and insert build-deps
#

scriptdir = os.path.dirname(os.path.realpath(sys.argv[0]))
with open(os.path.join(scriptdir, "Dockerfile.template")) as f:
    docker = f.read()
    template = string.Template(docker)

ai = []
bd = []
for p in projects:
    if p.name not in builddep:
        # install the package manager's builddeps for this project
        bd.append(namemap.get(p.name, p.name))
    else:
        l = builddep[p.name]
        if not l or l[0] != '+':
            # we have a list of builddeps (e.g. for projects not packaged)
            ai.extend(builddep[p.name])
        else:
            # install the package manager's builddeps for this project ...
            bd.append(namemap.get(p.name, p.name))
            # ... and we have a list of buildeps (e.g. if some are missing)
            ai.extend(builddep[p.name][1:])

with open(args.docker, 'w') as f:
    print(template.substitute(builddep = ' '.join(bd), alsoinstall = ' '.join(ai)), file=f)

#
# read template.yml and insert project list into build matrix
#

with open(os.path.join(scriptdir, "template.yaml")) as f:
    output = yaml.load(f)

matrix = [{'env': ['NAME=%s' % p.name, 'REPO=%s' % p.repo, 'BRANCH=%s' % p.branch]
                   + (['SOURCEDIR=%s' % p.sourcedir] if p.sourcedir else [])
                   + (['HACKS="%s"' % p.hacks] if p.hacks else [])} for p in projects]

output['matrix'] = {'include': matrix}

with open(args.yml, 'w') as f:
    print(yaml.dump(output, default_flow_style=False), file=f)
