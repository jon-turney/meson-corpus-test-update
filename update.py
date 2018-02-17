#!/usr/bin/env python3

#
# Construct a .travis.yml to run the git master of meson on the list of projects
#

import argparse
import collections
import os
import re
import sys
import urllib.request
import yaml

#
# argument parsing
#

parser = argparse.ArgumentParser('meson corupus test updater tool')
parser.add_argument('yml', help='.travis.yml file', metavar='YMLFILE')
args = parser.parse_args()

#
# static data
#

Project = collections.namedtuple('Project', ['name', 'repo', 'branch', 'builddep', 'alsoinstall', 'sourcedir', 'hacks'])

# map project names to source package names
namemap = {
    'glib' : 'glib2.0',
    'gtk+': 'gtk+4.0',
    'gstreamer': 'gstreamer1.0',
    'igt': 'intel-gpu-tools',
    'libfuse' : 'fuse',
    'pango': 'pango1.0',
    'xorg': 'xorg-server',
    'zstandard': 'zstd',
}

# build dependencies to use instead of, or as well as (if first is '+'), the builddeps from package manager
builddep = {
    'budgie-desktop': ['valac', 'libgtk-3-dev', 'libwnck-3-dev', 'libpeas-dev', 'uuid-dev', 'libibus-1.0-dev', 'libgnome-desktop-3-dev', 'libaccountsservice-dev', 'intltool'],
    'casync': ['+', 'libudev-dev'],
    'dpdk': [],
    'dbus-broker': ['python-docutils'],
    'emeus': ['libglib2.0-dev', 'libgtk-3-dev', 'libgirepository1.0-dev'],
    'fwupd': ['+', 'libjson-glib-dev', 'help2man'],
    'geary': ['+', 'libunwind-dev'],
    'gtkdapp': ['libgtkd-3-dev', 'gdc', 'gsettings-desktop-schemas-dev', 'libglib2.0-dev', 'gettext'],
    'hardcode-tray': ['libgirepository1.0-dev', 'libgtk-3-dev'],
    'jsoncpp': [],
    'hexchat': ['+', 'libluajit-5.1-dev'],
    'libfuse': ['+', 'udev'],
    'libhttpseverywhere': ['valac', 'libjson-glib-dev', 'libsoup2.4-dev', 'libgee-0.8-dev', 'libarchive-dev', 'gobject-introspection'],
    'libosmscout': [],
    'lightdm-webkit2-greeter': ['libdbus-glib-1-dev', 'liblightdm-gobject-1-dev', 'libgtk-3-dev', 'libwebkit2gtk-4.0-dev'],
    'kiwix-libraries': ['libzim-dev'],
    'mesa': ['+', 'libxvmc-dev', 'libomxil-bellagio-dev'],
    'miraclecast': ['libudev-dev', 'libglib2.0-dev', 'libsystemd-dev'],
    'nemo': ['+', 'libxapp-dev'],
    'outlier': [],
    'pango': ['+', 'libfribidi-dev'],
    'parzip': [],
    'pipewire': ['libdbus-1-dev', 'libasound2-dev', 'libv4l-dev', 'libudev-dev'],
    'pithos': ['+', 'libglib2.0-dev'],
    'sysprof': ['+', 'systemd'],
    'szl': [],
    'taisei-project': ['libsdl2-dev', 'libsdl2-ttf-dev', 'libsdl2-image-dev', 'libpng-dev', 'python-docutils'],
    'valum': ['valac', 'libsoup2.4-dev', 'libssl-dev'],
    'wayland-and-weston': ['libudev-dev', 'libmtdev-dev', 'libevdev-dev', 'libwacom-dev', 'doxygen', 'graphviz', 'libgtk-3-dev', 'check', 'valgrind'],
    'wlroots': ['libwayland-dev', 'libegl1-mesa-dev', 'wayland-protocols'],
    'xi-gtk': ['valac', 'libgtk-3-dev', 'libjson-glib-dev'],
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
    'https://lists.freedesktop.org/archives/wayland-devel/2016-November/031984.html': 'git://anongit.freedesktop.org/wayland/libinput', # not merged yet, try wayland-libinput instead...
    'https://github.com/facebook/zstd/commit/4dca56ed832c6a88108a2484a8f8ff63d8d76d91': 'https://github.com/facebook/zstd.git'
}

# blacklist of projects we don't attempt to build
blacklist = [
    'arduino-sample-project',  # work out how to setup cross-env
    'dxvk',  # work out how to install vulcan devkit
    'frida', # no meson.build ?!?
    'gnome-builder', # needs a later libdazzle than in artful
    'gnome-software', # needs a later appstream-glib than in artful
    'gtk+', # needs a later glib than in artful
    'kiwix-libraries', #  needs a later libzim than in artful
    'libgit2-glib', # needs a later libgit2 than in artful
    'mesa', # needs later deps than in artful
    'pitivi', # needs a later gstreamer-1.0 than in artful
    'sshfs', # needs a later libfuse than in artful
    'wlroots', # needs a later wayland-protocols than in artful
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
    'lightdm-webkit2-greeter': '''sed -i "s#'@0@/utils.sh'.format(meson.build_root())#join_paths(meson.source_root(), 'build/utils.sh')#" src/meson.build''',
    'parzip': 'meson wrap update zlib',
    'radare2': '(cd shlr; ./capstone.sh https://github.com/aquynh/capstone.git next)', # yes, I threw up in my mouth, a bit...
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

            # convert name to a form which is more likely to be a packagename
            name = name.lower().replace(' ','-')

            if name in blacklist:
                continue

            url = url_remap.get(url, url)

            # workaround freedesktop.org CA not in trusty (?)
            url = re.sub(r'http(s|)://cgit.freedesktop.org/', r'git://anongit.freedesktop.org/', url)

            if name not in builddep:
                # install the package manager's builddeps for this project
                bd = namemap.get(name, name)
                ai = None
            else:
                l = builddep[name]
                if not l or l[0] != '+':
                    # we have a list of builddeps (e.g. for projects not packaged)
                    bd = None
                    ai = builddep[name]
                else:
                    # install the package manager's builddeps for this project ...
                    bd = namemap.get(name, name)
                    # ... and we have a list of buildeps (e.g. if some are missing)
                    ai = builddep[name][1:]

            projects.append(Project(name = name,
                                    repo = url,
                                    builddep = bd,
                                    alsoinstall = ai,
                                    branch = branch_overrides.get(name, None),
                                    sourcedir = sourcedir.get(name, None),
                                    hacks = hacks.get(name, None)))

#
# read template.yml and insert project list into build matrix
#

scriptdir = os.path.dirname(os.path.realpath(sys.argv[0]))
with open(os.path.join(scriptdir, "template.yaml")) as f:
    output = yaml.load(f)

matrix = [{'env': ['NAME=%s' % p.name, 'REPO=%s' % p.repo]
                   + (['BRANCH=%s' % p.branch] if p.branch else [])
                   + (['BUILDDEP=%s' % p.builddep] if p.builddep else [])
                   + (['ALSOINSTALL="%s"' % ' '.join(p.alsoinstall)] if p.alsoinstall else [])
                   + (['SOURCEDIR=%s' % p.sourcedir] if p.sourcedir else [])
                   + (['HACKS="%s"' % p.hacks] if p.hacks else [])} for p in projects]

output['matrix'] = {'include': matrix}

with open(args.yml, 'w') as f:
    print(yaml.dump(output, default_flow_style=False, width=128), file=f)
