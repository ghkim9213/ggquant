with open('.etc/dbmaster_passwd.txt') as f:
    dbmaster_passwd = f.read().strip()

with open('.etc/dart_crtfc_key.txt') as f:
    dart_crtfc_key = f.read().strip()



DATABASES = {
    'default' : {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ggdb',
        'USER': 'master',
        'PASSWORD': dbmaster_passwd,
        'HOST': 'ggdb.cai2wlj5r9yu.ap-northeast-2.rds.amazonaws.com',
        'PORT': '3306',
    }
}
