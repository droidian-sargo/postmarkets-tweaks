import os
import configparser
from collections import OrderedDict

from pmos_tweaks.settingstree import SettingsTree


def main(version, datadir=None):
    # Read settings yaml files to build a whitelist of settings that are allowed to change
    # The daemon parameter makes it not load gtk components and skip gsettings things that won't
    # work as root
    st = SettingsTree(daemon=True)
    if datadir is not None:
        st.load_dir(os.path.join(datadir, 'postmarketos-tweaks'))
    st.load_dir('/etc/postmarketos-tweaks')
    settings = st.settings

    whitelist_sysfs = []

    for page in settings:
        for section in settings[page]['sections']:
            for setting in settings[page]['sections'][section]['settings']:
                s = settings[page]['sections'][section]['settings'][setting]
                if s.backend == 'sysfs':
                    whitelist_sysfs.append(s.key)

    # Read the stored settings and apply them
    config = configparser.ConfigParser()
    config.read('/etc/postmarketos-tweaks/tweakd.conf')

    # Apply sysfs settings
    if config.has_section('sysfs'):
        for path in config.options('sysfs'):
            if path not in whitelist_sysfs:
                print(f"Skipping {path}, not defined in setting definitions")
            value = config.get('sysfs', path)
            print(f"{path} = {value}")
            with open(path, 'w') as handle:
                handle.write(value)

    # Apply osk-sdl settings
    if config.has_section('osksdl'):
        oskconfig = OrderedDict()
        if os.path.isfile('/boot/osk.conf'):
            with(open('/boot/osk.conf')) as handle:
                for line in handle.readlines():
                    if line.startswith('#'):
                        continue
                    if ' = ' not in line:
                        continue
                    key, val = line.split(' = ')
                    oskconfig[key] = val.strip()

        for key in config.options('osksdl'):
            oskconfig[key] = config.get('osksdl', key).lower()

        result = '# Generated by postmarketos-tweaks\n\n'
        for key in oskconfig:
            result += f"{key} = {oskconfig[key]}\n"

        with open('/boot/osk.conf', 'w') as handle:
            handle.write(result)


if __name__ == '__main__':
    main(None)
