import os

from ConfigParser import SafeConfigParser, NoOptionError

def abs_path(path):
    path = os.path.expanduser(path)
    path = os.path.abspath(path)

    return path

def config_option(fn, section, option):
    try:
        return fn(section, option)
    except NoOptionError:
        return None

def config_list(config, section, option):
    try:
        list_ = config.get(section, option)
        list_ = list_.split(',')
        list_ = [option.strip() for option in list_]
        return list_
    except NoOptionError:
        return None

def config_parser(path):
    path = abs_path(path)
    config = SafeConfigParser()
    with open(path) as fp:
        config.readfp(fp)

    return config
