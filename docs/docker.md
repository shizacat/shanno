# Setup docker images

## Environments

* TZ - setup timezone, default Etc/UTC
* SH_PORT - the port will bind
* SH_WORKERS - the count of workers gunicorn
* SH_DEBUG - (True/False) mode have runing django
* SH_SECRET_KEY - secret key django
* SH_DATABASE_URL - URL for database. (sqlite:////var; postgresql://u:p@host:p/dn)
* SH_ADMIN_USERNAME; SH_ADMIN_PASSWORD; SH_ADMIN_EMAIL - Create super admin user.

## BUILD

```bash
docker build -t shanno -f contribute/docker/Dockerfile .
```

Test run

```bash
docker run -ti --rm -p 8000:8000 shanno
```
