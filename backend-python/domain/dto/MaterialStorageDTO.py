from flask import request
from pydantic import BaseModel, Field, ValidationError
from domain.dto.BaseDTO import BaseDTO
from typing import Optional

# 定义 DTO
class MaterialStorageDTO(BaseDTO):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, alias="pageSize", ge=1, le=100)
    is_non_order_material: int = Field(default=0, alias="isNonOrderMaterial", ge=0, le=1)
    material_name: Optional[str] = Field(alias="materialName", min_length=1, max_length=60, default=None)
    material_specification: Optional[str] = Field(alias="materialSpecification", min_length=1, max_length=100, default=None)
    material_model: Optional[str] = Field(alias="materialModel", min_length=1, max_length=50, default=None)
    material_color: Optional[str] = Field(alias="materialColor", min_length=1, max_length=40, default=None)
    supplier_name: Optional[str] = Field(alias="supplierName", min_length=1, max_length=100, default=None)
    order_rid: Optional[str] = Field(alias="orderRId", min_length=1, max_length=30, default=None)
    shoe_rid: Optional[str] = Field(alias="shoeRId", min_length=1, max_length=30, default=None)