from main import create_application
from a2wsgi import WSGIMiddleware

flask_app = create_application()
app = WSGIMiddleware(flask_app)

if __name__ == '__main__':
    flask_app.run()
