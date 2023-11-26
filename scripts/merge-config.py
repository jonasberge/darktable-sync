#!/usr/bin/python3

from argparse import ArgumentParser
from enum import Enum
from os import path
import os
import re
import sys
import tempfile
import shutil
import glob
import time


class Platform(Enum):
    linux = 'linux'
    windows = 'windows'

    def __str__(self):
        return self.value


class MergeOption(Enum):
    newest = 'newest'
    linux = 'linux'
    windows = 'windows'

    def __str__(self):
        return self.value
    
    @classmethod
    def to_platform(cls, value):
        if value.value == MergeOption.linux.value:
            return Platform.linux
        if value.value == MergeOption.windows.value:
            return Platform.windows
        raise ValueError('unable to determine platform from merge option')


def parse_args():
    parser = ArgumentParser(
        description='Merge two darktable config directories from a windows and a linux installation'
    )
    parser.add_argument(
        '--merge', '-m',
        type=MergeOption,
        default=MergeOption.newest,
        choices=list(MergeOption),
        help='set preference on which config to prefer when merging',
        required=True,
    )
    parser.add_argument(
        '--platform', '-p',
        type=Platform,
        choices=list(Platform),
        help='set the platform for which the merge is made',
        required=False,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--destination-directory', '-D',
        type=str,
        help='destination directory where merged files are written',
    )
    group.add_argument(
        '--destination-platform', '-d',
        type=Platform,
        choices=list(Platform),
        help='platform into whose config directory merged files are written',
    )
    parser.add_argument(
        '--linux-config', '-l',
        type=str,
        # nargs="?",
        help='path to the linux config directory',
        required=True,
    )
    parser.add_argument(
        '--windows-config', '-w',
        type=str,
        # nargs="?",
        help='path to the windows config directory',
        required=True,
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='do not do anything'
    )
    parser.add_argument(
        '--system-clock-delta', '-t',
        type=int,
        help='time difference between linux and windows system clocks in hours, used to properly determine which config directory is newer',
        default=0,
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='write informative messages'
    )
    args = parser.parse_args()
    if args.destination_platform == Platform.windows:
        args.destination_directory = args.windows_config
    if args.destination_platform == Platform.linux:
        args.destination_directory = args.linux_config
    if args.platform is None:
        if args.destination_platform is None:
            parser.error('either --platform or --destination-platform is required')
        args.platform = args.destination_platform
    return args


class MergeConfig:
    def __init__(self, *, keep_keys: list[str] = [], set_keys: dict[str, (str | dict[Platform, str])] = {}, allow_duplicates=False):
        self.keep_keys = keep_keys
        self.set_keys = set_keys
        self.allow_duplicates = allow_duplicates


SIMPLECONFIG_SPLITCHAR = '='

SHORTCUTSRC_FILENAMES = ['shortcutsrc', 'shortcutsrc.defaults', 'shortcutsrc.edit']
SHORTCUTSRC_MERGECONFIG = MergeConfig(
    allow_duplicates=True
)

DARKTABLERC_FILENAME = 'darktablerc'
DARKTABLERC_MERGECONFIG = MergeConfig(
    allow_duplicates=False,
    keep_keys=[
        r'cldevice.*',
        r'context_help.*',
        r'dt_cpubenchmark',
        r'opencl.*',
        r'plugins/darkroom/quick_preset_list', # for now...
        r'plugins/lighttable/collect/.*',
        r'plugins/lighttable/filtering/.*',
        r'plugins/lighttable/recentcollect/.*',
        r'plugins/lighttable/tagging/recent_tags',
        r'plugins/print/*',
        r'ui_last/color/.*_filename',
        r'ui_last/export_path',
        r'ui_last/import_custom_places',
        r'ui_last/import_last_directory',
        r'ui_last/import_last_image.*',
        r'ui_last/import_last_place',
        r'ui_last/window.*',
        r'database_cache_quality',
    ],
    set_keys={
        'plugins/darkroom/lut3d/def_path': {
            Platform.windows: 'D:\Fotografie\Vendor',
            Platform.linux: '/media/hdd/Fotografie/Vendor'
        },
        'session/base_directory_pattern': {
            Platform.windows: 'F:\Recordings\Tether',
            Platform.linux: '/media/photography/Recordings/Tether'
        },
        'plugins/darkroom/image_infos_pattern': '$(RATING_ICONS) $(LABELS_COLORICONS) <b>$(MAKER) $(MODEL) • $(LENS) • $(FILE_NAME).$(FILE_EXTENSION)</b> • <b>SS</b> $(EXIF_EXPOSURE) • <b>f</b>/$(EXIF_APERTURE) • $(EXIF_FOCAL_LENGTH) mm • <b>ISO</b> $(EXIF_ISO) • <b>Time:</b> $(EXIF_DAY).$(EXIF_MONTH).$(EXIF_YEAR:2:2) $(EXIF_HOUR):$(EXIF_MINUTE):$(EXIF_SECOND) • <b>Dimensions:</b> $(SENSOR_WIDTH)x$(SENSOR_HEIGHT) • <b>Export:</b> $(EXPORT_WIDTH)x$(EXPORT_HEIGHT) • <b>OpenCL:</b> $(OPENCL_ACTIVATED)',
        # 'plugins/imageio/storage/disk/file_directory': '$(FILE_FOLDER)/.darktable_export/$(FILE_NAME)',
        'plugins/imageio/storage/disk/overwrite': '0',
        'plugins/lighttable/extended_pattern': '$(FILE_NAME).$(FILE_EXTENSION)$(NL)$(EXIF_EXPOSURE) • f/$(EXIF_APERTURE) • $(EXIF_FOCAL_LENGTH)mm • $(EXIF_ISO) ISO $(SIDECAR_TXT)',
        'plugins/lighttable/thumbnail_tooltip_pattern': '<b>$(FILE_NAME).$(FILE_EXTENSION)</b>$(NL)$(EXIF_DAY)/$(EXIF_MONTH)/$(EXIF_YEAR) $(EXIF_HOUR):$(EXIF_MINUTE):$(EXIF_SECOND)$(NL)$(EXIF_EXPOSURE) • f/$(EXIF_APERTURE) • $(EXIF_FOCAL_LENGTH) mm • $(EXIF_ISO) ISO',
        'ui_last/import_dialog_show_home': 'false',
        'ui_last/import_dialog_show_mounted': 'false',
        'ui_last/import_dialog_show_pictures': 'false',
        'write_sidecar_files': 'after edit',
        'run_crawler_on_start': 'true',
        'plugins/darkroom/clipping/extra_aspect_ratios/5:4, 4x5, 2.5% frame': '503225806:400000000',
        'plugins/darkroom/clipping/extra_aspect_ratios/5:4, 4x5, 4% frame': '505263157:400000000',
        # 'plugins/darkroom/clipping/extra_aspect_ratios/16:10, 2.5% frame, experimental': '97596209:157596209',
    }
)

DATADB_FILENAME = 'data.db'


def merged_configfiles(primary_path: str, secondary_path: str, *, platform: Platform, merge_config: MergeConfig):
    def parse_file(filepath):
        if not path.exists(filepath):
            return {}
        with open(filepath, 'r', encoding="utf-8") as f:
            result = {}
            for key, value in [line.split(SIMPLECONFIG_SPLITCHAR, 1) for line in f.readlines()]:
                value = value.strip()
                if merge_config.allow_duplicates:
                    if key not in result:
                        result[key] = set()
                    result[key].add(value)
                else:
                    result[key] = value
            return result
    
    def dump_lines(lines):
        return '\n'.join(sorted(lines))

    # nothing needs to be merged, in case they are the same files
    # if primary_path == secondary_path:
    #     with open(primary_path, 'r', encoding="utf-8") as f:
    #         return f.read()

    primary = parse_file(primary_path)
    secondary = parse_file(secondary_path)
    merged = dict(primary)

    def add_merged_value(value):
        if merge_config.allow_duplicates:
            if key not in merged:
                merged[key] = set()
            if isinstance(value, set):
                merged[key].update(value)
            else:
                merged[key].add(value)
        else:
            merged[key] = value

    for key, old_value in secondary.items():
        new_value = primary.get(key, old_value)
        keep_value = False
        if not merge_config.allow_duplicates:
            for regex in merge_config.keep_keys:
                if re.match(regex, key):
                    keep_value = True
                    break
        if keep_value:
            add_merged_value(old_value)
        else:
            add_merged_value(new_value)
    
    # delete any key which wasn't kept from the secondary
    # and should thus be removed if it was taken from the primary.
    if not merge_config.allow_duplicates:
        for key, value in primary.items():
            if key not in secondary:
                for regex in merge_config.keep_keys:
                    if re.match(regex, key):
                        del merged[key]

    # overwrite keys and make sure they exist in the output
    for key, target in merge_config.set_keys.items():
        if isinstance(target, dict):
            value = target[platform]
        else:
            value = target
        print('->', key, value)
        add_merged_value(value)

    content_lines = None
    if merge_config.allow_duplicates:
        content_lines = [f'{key}={value}' for key, value_set in merged.items() for value in value_set]
    else:
        content_lines = [f'{key}={value}' for key, value in merged.items()]

    return dump_lines(content_lines)


BAK_FILE_EXTENSION='.bak'
KEEP_BAKS_COUNT=4


def copy_file_safe(source_filepath, destination_filepath):
    print(f'writing: {destination_filepath}')

    def get_bak_filepath(number):
        return destination_filepath + BAK_FILE_EXTENSION + str(number)
    def get_bak_files():
        return glob.glob(destination_filepath + BAK_FILE_EXTENSION + '*')

    if path.exists(destination_filepath):
        counter = 1
        min_counter = sys.maxsize
        for file in get_bak_files():
            parts = file.split(BAK_FILE_EXTENSION)
            number_str: str = parts[len(parts) - 1] if len(parts) >= 2 else ''
            if number_str.isnumeric():
                number = int(number_str)
                counter = max(counter, number)
                min_counter = min(min_counter, number)
        while os.path.exists(get_bak_filepath(counter)):
            counter += 1
        shutil.copyfile(destination_filepath, get_bak_filepath(counter))
        for index in range(min_counter, counter - KEEP_BAKS_COUNT + 1):
            try:
                os.remove(get_bak_filepath(index))
            except OSError:
                pass
    
    shutil.copy(source_filepath, destination_filepath)


def write_plaintext_content_safe(content, destination_filepath, *, encoding='utf-8'):
    tmp_filename = None
    with tempfile.NamedTemporaryFile(mode='w', encoding=encoding, delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
    os.makedirs(path.dirname(destination_filepath), exist_ok=True)
    copy_file_safe(tmp.name, destination_filepath)
    tmp_filename = tmp.name
    try:
        os.remove(tmp_filename)
    except OSError as e:
        print(e)


def get_newest_config_dir(linux_config_dir: str, windows_config_dir: str, delta_hours: int = 0):
    print('>> determining newest config directory')

    linux_mtime = path.getmtime(path.join(linux_config_dir, DARKTABLERC_FILENAME))
    windows_mtime = path.getmtime(path.join(windows_config_dir, DARKTABLERC_FILENAME))
    linux_mtime_corrected = linux_mtime - 60 * 60 * delta_hours
    print('linux time (before applying delta):', time.ctime(linux_mtime))
    print('linux time (after applying delta):', time.ctime(linux_mtime_corrected))
    print('windows time:', time.ctime(windows_mtime))

    newest_platform = Platform.linux if linux_mtime_corrected >= windows_mtime else Platform.windows
    print('newer platform:', newest_platform)
    return newest_platform


def main(merge: MergeOption, platform: Platform, destination_directory: str, linux_config_dir: str, windows_config_dir: str):
    print('>> merging')
    config_dirs = {
        Platform.linux: linux_config_dir,
        Platform.windows: windows_config_dir,
    }

    primary: Platform = MergeOption.to_platform(merge)
    secondary: Platform = platform

    # darktablerc
    # even if we are on the same platform, write it again,
    # so that above config parameters are applied in case they are changed.
    primary_darktablerc = path.join(config_dirs[primary], DARKTABLERC_FILENAME)
    secondary_darktablerc = path.join(config_dirs[secondary], DARKTABLERC_FILENAME)
    darktablerc_content = merged_configfiles(primary_darktablerc, secondary_darktablerc, platform=platform, merge_config=DARKTABLERC_MERGECONFIG)
    write_plaintext_content_safe(darktablerc_content, path.join(destination_directory, DARKTABLERC_FILENAME))

    if primary == secondary:
        print(f'>> same platform ({primary} and {secondary}), nothing to do')
        exit(0)

    # shortcutsrc's
    for shortcutsrc_filename in SHORTCUTSRC_FILENAMES:
        primary_shortcutsrc = path.join(config_dirs[primary], shortcutsrc_filename)
        secondary_shortcutsrc = path.join(config_dirs[secondary], shortcutsrc_filename)
        shortcutsrc_content = merged_configfiles(primary_shortcutsrc, secondary_shortcutsrc, platform=platform, merge_config=SHORTCUTSRC_MERGECONFIG)
        write_plaintext_content_safe(shortcutsrc_content, path.join(destination_directory, shortcutsrc_filename))

    # data.db's
    primary_datadb = path.join(config_dirs[primary], DATADB_FILENAME)
    secondary_datadb = path.join(destination_directory, DATADB_FILENAME)
    copy_file_safe(primary_datadb, secondary_datadb)


if __name__ == '__main__':
    args = parse_args()
    if args.dry_run or args.debug:
        print('>> program arguments')
        for key, value in vars(args).items():
            print(f'{key}: {value}')
    if args.merge == MergeOption.newest:
        # TODO: choose the folder with the most recent changes
        args.merge = get_newest_config_dir(
            linux_config_dir=args.linux_config,
            windows_config_dir=args.windows_config,
            delta_hours=args.system_clock_delta
        )
    if not args.dry_run:
        main(
            merge=args.merge,
            platform=args.platform,
            destination_directory=args.destination_directory,
            linux_config_dir=args.linux_config,
            windows_config_dir=args.windows_config
        )

# https://www.howtogeek.com/323390/how-to-fix-windows-and-linux-showing-different-times-when-dual-booting/
