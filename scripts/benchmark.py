#!/usr/bin/python3
import argparse
import json
import subprocess

from monotonic import monotonic

from detect_secrets.core.usage import PluginOptions


def main():
    args = get_arguments()

    # First, convert chosen plugins into their disabled flags
    always_disabled_plugins = []
    flag_list = []
    for info in PluginOptions.all_plugins:
        if info.classname in args.plugin:
            flag_list.append(info.disable_flag_text)
        else:
            always_disabled_plugins.append(info.disable_flag_text)

    # Then, iterate through each disabled flag, toggling them off
    # individually.
    timings = {}
    if len(args.plugin) == len(PluginOptions.all_plugins):
        # Only run benchmarks for all the cases, if already running all plugins
        timings['all-plugins'] = time_execution(
            filenames=args.filenames,
            timeout=args.harakiri,
        )

    for flag_number, flag in enumerate(flag_list):
        plugins_to_ignore = list(flag_list)
        plugins_to_ignore.pop(flag_number)

        key = flag[len('--no-'):-len('-scan')]
        timings[key] = time_execution(
            filenames=args.filenames,
            timeout=args.harakiri,
            flags=plugins_to_ignore + always_disabled_plugins,
        )

    print_output(timings, args)


def get_arguments():
    plugins = [
        info.classname
        for info in PluginOptions.all_plugins
    ]

    parser = argparse.ArgumentParser(description='Run some benchmarks.')
    parser.add_argument(
        'filenames',
        nargs=argparse.REMAINDER,
        help='Filenames to check or detect-secrets compatible arguments.',
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Human readable output.',
    )
    parser.add_argument(
        '--plugin',
        default=None,       # needs to be None, otherwise append won't work as expected
        choices=plugins,
        action='append',
        help=(
            'Specifies a plugin to test. May provide multiple values. '
            'Defaults to all.'
        ),
    )
    parser.add_argument(
        '--harakiri',
        default=5,
        type=float,
        help=(
            'Specifies an upper bound for the number of seconds to wait '
            'per execution.'
        ),
    )

    args = parser.parse_args()
    if not args.filenames:
        args.filenames = ['../.']

    if not args.plugin:
        args.plugin = plugins

    return args


def time_execution(filenames, timeout, flags=None):
    """
    :type filenames: list
    :type timeout: float

    :type flags: list|None
    :param flags: flags to disable
    """
    if not flags:
        flags = []

    start_time = monotonic()
    try:
        subprocess.check_output(
            'detect-secrets scan'.split() + filenames + flags,
            timeout=timeout,
        )
        return monotonic() - start_time
    except subprocess.TimeoutExpired:
        pass


def print_output(timings, args):
    """
    :type timings: dict
    :type args: Namespace
    """
    if not args.pretty:
        print(json.dumps(timings))
        return

    # Print header
    print('Scanning: ' + str(args.filenames))
    print('-' * 42)
    print('{:<20s}{:>20s}'.format('plugin', 'time'))
    print('-' * 42)

    if 'all-plugins' in timings:
        print_line('all-plugins', timings['all-plugins'])
        del timings['all-plugins']

    for key in sorted(timings):
        print_line(key, timings[key])


def print_line(name, time):
    if not time:
        time = 'Timeout exceeded!'
    else:
        time = '{}s'.format(str(time))

    print('{:<20s}{:>20s}'.format(name, time))


if __name__ == '__main__':
    main()
