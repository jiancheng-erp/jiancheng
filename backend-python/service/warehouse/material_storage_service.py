from domain.dto.MaterialStorageDTO import MaterialStorageDTO
from domain.vo.MaterialStorageVO import MaterialStorageVO
from repositories.warehouse.material_storage_repository import MaterialStorageRepository


class MaterialStorageService:
    def __init__(self, repo: MaterialStorageRepository | None = None):
        self.repo = repo or MaterialStorageRepository()

    def get_all_material_info(self, param: MaterialStorageDTO):
        response, count_result = self.repo.get_material_storages(param)
        result = []
        for row in response:
            obj = MaterialStorageVO.model_validate(row)
            result.append(obj.model_dump(mode='json', by_alias=True))
        return result, count_result