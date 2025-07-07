from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from logger import logger


def sync_schema(app, db):
    """Syncs the database schema with Flask-SQLAlchemy models while keeping data persistent."""
    with app.app_context():
        connection = db.engine.connect()
        inspector = inspect(db.engine)

        # Loop through all tables defined in db.metadata
        # logger.debug(db.metadata.tables.keys())
        for table_name in db.Model.metadata.tables.keys():
            logger.debug(f"\nChecking table: {table_name}")

            # Step 1: Create table if it does not exist
            if table_name not in inspector.get_table_names():
                logger.debug(f"Table '{table_name}' does not exist. Creating it...")
                db.create_all()  # Creates only missing tables
                continue

            # Get column information
            existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
            model_columns = {c.name for c in db.metadata.tables[table_name].columns}

            # Step 2: Add missing columns
            missing_columns = model_columns - existing_columns
            for column_name in missing_columns:
                column_obj = db.metadata.tables[table_name].columns[column_name]
                nullable = "NULL" if column_obj.nullable else "NOT NULL"
                default_value = ""
                if column_obj.default is not None:
                    default_value = f" DEFAULT '{column_obj.default.arg}'"
                alter_stmt = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_obj.type} {nullable}{default_value}"
                logger.debug(f"Adding missing column: {column_name} to {table_name}")
                connection.execute(text(alter_stmt))

            # Step 3: modify columns
            # existing_columns = [col for col in inspector.get_columns(table_name)]
            # logger.debug(existing_columns)
            # for attribute_mapping in existing_columns:
            #     column_name = attribute_mapping['name']
            #     model_column_obj = db.metadata.tables[table_name].columns[column_name]
            #     if attribute_mapping['type'] != model_column_obj.type:
            #         logger.debug(f"Modifying column: {column_name} in {table_name}")
            #         alter_stmt = f"ALTER TABLE {table_name} CHANGE COLUMN {column_name} {model_column_obj.type}"
            #         connection.execute(text(alter_stmt))

            # Step 4: Identify and handle removed columns
            removed_columns = existing_columns - model_columns
            for column_name in removed_columns:
                logger.debug(f"Warning: Column '{column_name}' exists in DB but is missing in the model for table '{table_name}'.")

                # Check if column contains data before deletion
                result = connection.execute(text(f"SELECT COUNT(*) FROM `{table_name}` WHERE `{column_name}` IS NOT NULL")).fetchone()
                if result and result[0] > 0:
                    logger.debug(f"Error: Cannot remove column '{column_name}' from table '{table_name}' because it contains data. Ignore this column...")
                    break

                # Safe removal if no data exists
                try:
                    connection.execute(text(f"ALTER TABLE `{table_name}` DROP COLUMN `{column_name}`"))
                    logger.debug(f"Column '{column_name}' has been removed from {table_name}.")
                except SQLAlchemyError as e:
                    logger.debug(f"Failed to drop column '{column_name}' from {table_name}: {e}")

        connection.close()
        logger.debug("\nDatabase schema sync complete.")

# # Run schema synchronization
# if __name__ == "__main__":
#     sync_schema()
