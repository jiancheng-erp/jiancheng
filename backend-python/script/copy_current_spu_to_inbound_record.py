from app_config import db
from models import InboundRecordDetail, MaterialStorage, SizeMaterialStorage

def update_spu_material_id(app):
    updated_count = 0

    with app.app_context():
        inbound_details = InboundRecordDetail.query.all()

        for detail in inbound_details:
            if detail.material_storage_id:
                material_row = MaterialStorage.query.get(detail.material_storage_id)
                if material_row and material_row.spu_material_id is not None:
                    detail.spu_material_id = material_row.spu_material_id
                    updated_count += 1

            elif detail.size_material_storage_id:
                size_material_row = SizeMaterialStorage.query.get(detail.size_material_storage_id)
                if size_material_row and size_material_row.spu_material_id is not None:
                    detail.spu_material_id = size_material_row.spu_material_id
                    updated_count += 1

        db.session.commit()
        print(f"Updated {updated_count} InboundRecordDetail records with spu_material_id.")
