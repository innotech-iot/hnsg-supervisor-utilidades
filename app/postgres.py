"""Connection arguments for libpq clients without a password in process argv."""
import os


def client_connection(url):
    env=os.environ.copy()
    password=url.query.get('password',url.password)
    if password is not None:
        if not isinstance(password,str):raise ValueError('Senha PostgreSQL deve ser um valor único')
        env['PGPASSWORD']=password
    # URL.set ignores None; _replace actually removes the authority password.
    public_url=url.difference_update_query(['password'])._replace(drivername='postgresql',password=None)
    return public_url.render_as_string(hide_password=False),env
