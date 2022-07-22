with open('.etc/ggdb_passwd.txt') as f:
    ggdb_passwd = f.read().strip()

with open('.etc/dart_crtfc_key.txt') as f:
    dart_crtfc_key = f.read().strip()

with open('.etc/ggdb_endpoint.txt') as f:
    ggdb_endpoint = f.read().strip()

DATABASES = {
    'default' : {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ggdb',
        'USER': 'master',
        'PASSWORD': dbmaster_passwd,
        'HOST': ggdb_endpoint,
        'PORT': '3306',
    }
}
