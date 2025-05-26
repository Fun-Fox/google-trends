import configparser
import os.path
from webui.utils.constant import root_dir

def load_regions_choices():
    config = configparser.ConfigParser()
    with open(os.path.join(root_dir, 'webui/conf.ini'), encoding='utf-8') as config_file:
        config.read_file(config_file)

    regions = {k: v for k, v in config['regions'].items()}
    category_names = {k: v for k, v in config['category_names'].items()}

    return {
        'regions': regions,
        'category_names': category_names
    }