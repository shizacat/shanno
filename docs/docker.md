# Setup docker images

## Environments

<!-- * TZ - setup timezone, default GMT -->
* SH_PORT - порт на котором будет работать
* SH_WORKERS - количество воркеров gunicorn
* SH_DEBUG - (True/False) режим запуска django
* SH_SECRET_KEY - секретный ключ django
* SH_DATABASE_URL - URL для базы данных. (sqlite:////var; postgresql://u:p@host:p/dn)
* SH_ADMIN_USERNAME; SH_ADMIN_PASSWORD; SH_ADMIN_EMAIL - Create super admin user.

## BUILD

```bash
docker build -t shanno -f contribute/docker/Dockerfile .
```

Test run

```bash
docker run -ti --rm -p 8000:8000 shanno
```
