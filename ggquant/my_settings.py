with open('.etc/dbmaster_pwd.txt') as f:
    dbmaster_pwd = f.read().strip()

with open('.etc/dart_crtfc_key.txt') as f:
    dart_crtfc_key = f.read().strip()



DATABASES = {
    'default' : {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ggquant',
        'USER': 'master',
        'PASSWORD': dbmaster_pwd,
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
