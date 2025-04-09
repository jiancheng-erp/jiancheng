from models import *
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from file_locations import FILE_STORAGE_PATH, IMAGE_UPLOAD_PATH
import os

def rename_file_storage_path_names(app, db):
    print("Renaming file storage path names...")
    with app.app_context():
        orders = db.session.query(Order).all()
        for order in orders:
            order_rid = order.order_rid
            order_id = order.order_id
            # rename the directory name
            old_dir_name = FILE_STORAGE_PATH + "/"+ str(order_rid) + "/"
            new_dir_name = FILE_STORAGE_PATH + "/"+ str(order_id) + "/"
            if os.path.exists(old_dir_name):
                os.rename(old_dir_name, new_dir_name)
            old_dir_name = IMAGE_UPLOAD_PATH + "/"+ str(order_rid) + "/"
            new_dir_name = IMAGE_UPLOAD_PATH + "/"+ str(order_id) + "/"
            if os.path.exists(old_dir_name):
                os.rename(old_dir_name, new_dir_name)
        #loop all the shoe_type, the shoe_type has a column called shoe_image_url,it is like this:
        # shoe/C230571(it is shoe_rid)/棕色/1.jpg, now i want to change it to shoe/(shoe_id)/棕色/1.jpg
        shoe_types = db.session.query(ShoeType).all()
        for shoe_type in shoe_types:
            if shoe_type.shoe_image_url:
                # get the shoe_id from the shoe_image_url
                shoe_rid = shoe_type.shoe_image_url.split("/")[1]
                # get the shoe_id from the database
                shoe = db.session.query(Shoe).filter(Shoe.shoe_rid == shoe_rid).first()
                if shoe:
                    shoe_id = shoe.shoe_id
                else:
                    print(f"Error: shoe with shoe_rid {shoe_rid} not found.")
                    continue
                # rename the file storage path name
                new_shoe_image_url = shoe_type.shoe_image_url.replace(shoe_rid, str(shoe_id))
                shoe_type.shoe_image_url = new_shoe_image_url
                db.session.flush()
        #you should also renamed the dictory name in the file system, the directory name is like this:
        #IMAGE_UPLOAD_PATH + "shoe/" + str(shoe_id) + "/"
        #but the file system is not in the database, so you should use os.rename to rename the directory name
        #and the file name is like this:
        #IMAGE_UPLOAD_PATH + "shoe/" + str(shoe_id) + "/棕色/1.jpg"
        shoes = db.session.query(Shoe).all()
        for shoe in shoes:
            shoe_rid = shoe.shoe_rid
            shoe_id = shoe.shoe_id
            #rename the directory name
            old_dir_name = IMAGE_UPLOAD_PATH + "/shoe/" + str(shoe_rid) + "/"
            new_dir_name = IMAGE_UPLOAD_PATH + "/shoe/" + str(shoe_id) + "/"
            if os.path.exists(old_dir_name):
                os.rename(old_dir_name, new_dir_name)
            #it will be a path like FILE_STORAGE_PATH + "/"+ str(order_id) + str(shoe_rid)
            #rename the dictory name
            order_shoe = db.session.query(OrderShoe).filter(OrderShoe.shoe_id == shoe_id).all()
            for order_shoe in order_shoe:
                order_id = order_shoe.order_id
                old_dir_name = FILE_STORAGE_PATH + "/"+ str(order_id) + "/" + str(shoe_rid) + "/"
                new_dir_name = FILE_STORAGE_PATH + "/"+ str(order_id) + "/" + str(shoe_id) + "/"
                if os.path.exists(old_dir_name):
                    os.rename(old_dir_name, new_dir_name)
                old_dir_name = IMAGE_UPLOAD_PATH + "/"+ str(order_id) + "/" + str(shoe_rid) + "/"
                new_dir_name = IMAGE_UPLOAD_PATH + "/"+ str(order_id) + "/" + str(shoe_id) + "/"
                if os.path.exists(old_dir_name):
                    os.rename(old_dir_name, new_dir_name)
        #commit the changes to the database
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error committing changes: {e}")
        finally:
            db.session.close()
    print("Renaming file storage path names completed.")
            

            
        
        