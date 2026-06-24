"""
run.py — Application entry point.

Used by:
  - Flask CLI: `flask run`
  - Gunicorn:  `gunicorn run:app`
  - Docker entrypoint: `flask run --host=0.0.0.0`
"""
import os

from app import create_app

# Map FLASK_ENV value to internal config key
_env = os.environ.get('FLASK_ENV', 'development')
_config_map = {
    'development': 'development',
    'production':  'production',
    'testing':     'testing',
}
config_name = _config_map.get(_env, 'development')

app = create_app(config_name)

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=(config_name == 'development'),
    )
