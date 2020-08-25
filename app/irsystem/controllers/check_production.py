import os


def filepath():
    # if is_development():
    #print("making filepath")
    #print(os.environ.get('APP_SETTINGS') == "config.DevelopmentConfig")
    if os.environ.get('APP_SETTINGS') == "config.DevelopmentConfig":
        return './app/irsystem/controllers/'
    else:
        return '/app/app/irsystem/controllers/'
