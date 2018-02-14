#!/usr/bin/env python3

#
# Construct a .travis.yml to run the git master of meson on the list of projects
#

import collections
import re
import sys
import yaml
import urllib.request

Project = collections.namedtuple('Project', ['name', 'repo', 'branch', 'builddep'])

builddep = {
    'aqemu': ['qtbase5-dev', 'libvncserver-dev'],
    'budgie_desktop': ['valac', 'libgtk-3-dev'],
    'casync': ['libzstd-dev'],
    'cinnamon-desktop': ['libgtk-3-dev', 'libxkbfile-dev', 'libpulse-dev', 'gobject-introspection', 'libgirepository1.0-dev'],
    'dbus-broker': ['python-docutils'],
    'geary': ['valac'],
    'glib': ['libmount-dev'],
    'gnome_builder': ['libdazzle-1.0-dev'],
    'gnome_mpv': ['libgtk-3-dev'],
    'gnome_recipes': ['libsoup2.4-dev', 'libgoa-1.0-dev'],
    'gnome_software': ['libappstream-glib-dev'],
    'gnome_twitch': ['libgtk-3-dev'],
    'gtkdapp': ['gdc', 'libgtkd-3-dev'],
    'hardcode-tray': ['libgirepository1.0-dev', 'libgtk-3-dev'],
    'hexchat': ['libproxy-dev', 'libcanberra-dev', 'libdbus-glib-1-dev', 'libgtk2.0-dev', 'libnotify-dev', 'libluajit-5.1-dev'],
    'libdrm': ['libpciaccess-dev'],
    'libhttpseverywhere': ['valac', 'libjson-glib-dev', 'libsoup2.4-dev'],
    'lightdm-webkit2-greeter': ['libdbus-glib-1-dev', 'liblightdm-gobject-1-dev'],
    'kiwix_libraries': ['libzim-dev'],
    'miraclecast': ['libudev-dev', 'libsystemd-dev'],
    'nemo': ['libgtk-3-dev', 'libgirepository1.0-dev'],
    'outlier': ['libxml2-dev'],
    'orc': [],
    'pango': ['libfribidi-dev'],
    'pipewire': ['libdbus-1-dev'],
}

url_remap = {
    'http://dpdk.org/ml/archives/dev/2018-January/089724.html': 'git://dpdk.org/dpdk',
    'https://www.frida.re/': 'https://github.com/frida/frida.git',
    'https://wiki.gnome.org/Apps/Geary': 'https://git.gnome.org/browse/geary',
    'https://ebassi.github.io/graphene/': 'git://github.com/ebassi/graphene',
    'https://mail.gnome.org/archives/grilo-list/2017-February/msg00000.html': 'https://git.gnome.org/browse/grilo',
    'https://github.com/grindhold/libhttpseverywhere': 'https://git.gnome.org/browse/libhttpseverywhere',  # moved
    'https://www.mesa3d.org/': 'git://anongit.freedesktop.org/mesa/mesa',
    'https://git.gnome.org/browse/nautilus/commit/?id=ed5652c89ac0654df2e82b54b00b27d51c825465': 'https://gitlab.gnome.org/GNOME/nautilus.git',
    'https://pipewire.org/': 'https://github.com/PipeWire/pipewire.git',
}

blacklist = [
    'arduino_sample_project',  # work out how to setup cross-env
    'budgie_desktop',  # needs a later glib than in trusty
    'casync',  # zstd not in trusty?
    'dxvk',  # work out how to install vulcan devkit
    'emeus', # needs a later glib than in trusty
    'frida', # no meson.build in top-level directory ?!?
    'fwupd', # needs a later gio than in trusty
    'geary', # needs a later glib than in trusty
    'glib',  # needs a later libmount than in trusty
    'gnome_builder', # needs libdazzle, not in trusty
    'gnome_mpv', # needs a later glib than in trusty
    'gnome_software', # need libappstream-glib, not in trusty
    'gnome_twitch', # needs a later glib than in trusty
    'grilo', # needs a later gio than in trusty
    'gtk+', # fallsback to building glib, then fails to use it...
    'gtkdapp', # needs libgtkd-3-dev, not in trusty
    'igt', # needs a later libdrm than in trusty
    'json-glib', # needs later gobject than in trusty
    'libgit2-glib', # needs a later glib than in trusty
    'mesa', # needs later libdrm than in trusty
    'pango', # needs later fribidi than in trusty
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

# fetch project list, extract projects
project_list_url = "https://raw.githubusercontent.com/mesonbuild/meson/master/docs/markdown/Users.md"
content = urllib.request.urlopen(project_list_url).read().decode()

projects = []
for l in content.splitlines():
    m = re.search(r'\[(.*?)\]\((.*?)\)', l)
    if m:
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
                                branch = branch_overrides.get(name, 'master')))

# XXX: truncate
projects = projects[10:]

# read template.yaml and insert project list into build matrix
with open("template.yaml", 'r') as f:
    output = yaml.load(f)

matrix = [{'env': ['NAME=%s' % p.name, 'REPO=%s' % p.repo, 'BRANCH=%s' % p.branch],
           'addons': { 'apt': {'packages': p.builddep + ['ninja-build'] }}} for p in projects]

output['matrix'] = {'include': matrix}

print(yaml.dump(output, default_flow_style=False))
