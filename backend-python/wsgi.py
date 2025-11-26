from main import app
from event_processor import EventProcessor

app.config['event_processor'] = EventProcessor()
if __name__ == "__main__":
    # only used for local development
    app.run(host="0.0.0.0", port=8000, debug=True)