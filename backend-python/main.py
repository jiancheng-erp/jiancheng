# main.py
# from api_utility import *
from app_config import create_app
from blueprints import register_blueprints
from mock_data_gen import *
from models import *
from event_processor import EventProcessor
from update_db import sync_schema
# from script.refresh_craft_name import refresh_storage_craft_match_craft_sheet
# from script.refresh_default_craft_sheet import refresh_default_craft_sheet
# from script.refresh_default_bom import refresh_default_bom
# from script.format_space_and_color_stynax import format_space_and_color_stynax
# from script.refresh_correct_size_material_amount_in_bom import refresh_correct_size_material_amount_in_bom


def get_app():
    app = create_app()
    register_blueprints(app)
    return app


app = get_app()

def main():
    # Create a new Flask app using the factory.

    # Register blueprints. You may need to update your register_blueprints function
    # to accept the app as a parameter.
    # Set additional configuration or attach objects.
    app.config['event_processor'] = EventProcessor()
    # sync_schema(app, db)
    # refresh_storage_craft_match_craft_sheet(app, db)
    # refresh_default_craft_sheet(app, db)
    # refresh_default_bom(app, db)
    # format_space_and_color_stynax(app, db)
    # refresh_correct_size_material_amount_in_bom(app, db)

    # Run the Flask app.
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)

if __name__ == "__main__":

    # Set additional configuration or attach objects.
    app.config['event_processor'] = EventProcessor()
    # sync_schema(app, db)
    # refresh_storage_craft_match_craft_sheet(app, db)
    # refresh_default_craft_sheet(app, db)
    # refresh_default_bom(app, db)
    # format_space_and_color_stynax(app, db)
    # refresh_correct_size_material_amount_in_bom(app, db)

    # Run the Flask app.
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)