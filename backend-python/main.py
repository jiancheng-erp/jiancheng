from flask_cors import CORS

from api_utility import *
from app_config import app, db
from blueprints import register_blueprints
from mock_data_gen import *
from models import *
from event_processor import EventProcessor
from update_db import sync_schema
from script.refresh_craft_name import refresh_storage_craft_match_craft_sheet
from script.refresh_default_craft_sheet import refresh_default_craft_sheet
from script.refresh_default_bom import refresh_default_bom


@app.route("/")
def hello_world():
    return "Hello World"


def main():
    """Main function to run the Flask application."""
    # Register all blueprints
    register_blueprints()
    # Run the Flask app
    app.run(
        host="0.0.0.0", port=8000, debug=True, threaded=True
    )  # Set debug as per your development needs


if __name__ == "__main__":
    event_processor = EventProcessor()
    app.config['event_processor'] = event_processor
    # sync_schema(app, db)
    # refresh_storage_craft_match_craft_sheet(app, db)
    # refresh_default_craft_sheet(app, db)
    refresh_default_bom(app, db)
    # event_processor.testPaths()
    # with app.app_context():
    # db.create_all()  # This will create the database tables under the application context.
    # shoes_rid = ["0E21922", "000000", "111111","222222"]
    # customer_name = ["Spain Customer 36", "Milan Customer 30", "Spain Customer 39", "Spain Customer 40"]
    # TestPopulateEndEntityDB(shoes_rid, customer_name)
    # TestPopulateOrdersDB(firstTime=True, reset = False)
    # with app.app_context():
            
    #     datagen = MockDataGenerator(db)
    #     datagen.cleanAndSetup()
    #     datagen.initializeEntityDataPath()
    #     datagen.setupDBLocalData(terminating_layer=7)
    # with app.app_context():
    #     processorTest = EventProcessor()
    #     processorTest.testPaths()
    #     processorTest.processEvent(Event(event_id = 10,staff_id = 1, handle_time = "2024-07-30",
    #                                      operation_id = 43,event_order_id = 0,event_order_shoe_id = 1))
    #             # operation 103 changes status 32 to 2
    #     mock_event = Event(event_id = 41, staff_id = 1,handle_time = "2024-07-02",
    #                             operation_id = 121,event_order_id = 4,event_order_shoe_id =11)
    #     ops_id_list = [38,39,40,41
                       
    #                    ,42,43,44,45,56,57,58,59,
    #                    72,73

    #                    ,74,75,

    #                    76,77,
    #                    78,79,80,81,82,83,

    #                    84,85,86,87,

    #                    88,89,90,91,
    #                    92,93,94,95,96,97,

    #                    98,99,100,101,102,103,104,105,

    #                    106,107,108,109,110,111,
    #                    112,113,114,115,116,117,

    #                    118,119,120,

    #     ]
    #     result = processorTest.processEvent(mock_event)
    #     if result:
    #         print("Event Processed")
    #     else:
    #         print("Event Invalid")
        # for i in range(38, 58,1 ):
        #     mock_event.operation_id = i
        #     processorTest.processEvent(mock_event)
    main()
