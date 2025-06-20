from app_config import db
from models import InboundRecordDetail, MaterialStorage, OutboundRecordDetail

def update_spu_material_id(app):
    updated_count1 = 0
    updated_count2 = 0

    with app.app_context():
        inbound_details = InboundRecordDetail.query.all()
        outbound_details = OutboundRecordDetail.query.all()
        for detail in inbound_details:
            if detail.material_storage_id:
                material_row = MaterialStorage.query.get(detail.material_storage_id)
                if material_row and material_row.spu_material_id is not None:
                    detail.spu_material_id = material_row.spu_material_id
                    updated_count1 += 1
        for detail in outbound_details:
            if detail.material_storage_id:
                material_row = MaterialStorage.query.get(detail.material_storage_id)
                if material_row and material_row.spu_material_id is not None:
                    detail.spu_material_id = material_row.spu_material_id
                    updated_count2 += 1

        db.session.commit()
        print(f"Updated {updated_count1} InboundRecordDetail records and {updated_count2} OutboundRecordDetail records with spu_material_id.")
