import os
from app import create_app, db
from flask_migrate import Migrate

from app.models import (user, member, group, Permission, role)

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db = db, user = user, member = member, group = group, app = app, 
            Permission = Permission, role = role)

if __name__ == '__main__':
    app.run(PORT = 8000)
