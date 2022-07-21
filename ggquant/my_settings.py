with open('.etc/dbmaster_passwd.txt') as f:
    dbmaster_pwd = f.read().strip()

with open('.etc/dart_crtfc_key.txt') as f:
    dart_crtfc_key = f.read().strip()



DATABASES = {
    'default' : {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ggdb',
        'USER': 'master',
        'PASSWORD': dbmaster_passwd,
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
