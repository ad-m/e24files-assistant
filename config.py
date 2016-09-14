def get_access_pair(config, section):
    return (config.get(section, 'access_key'), config.get(section, 'secret_key'))
