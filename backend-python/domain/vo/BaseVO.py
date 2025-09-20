from pydantic import BaseModel, Field, ConfigDict

def camel(s: str) -> str:
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])

class BaseVO(BaseModel):
    # 允许从 ORM 对象读取属性；by_alias 输出 camelCase
    model_config = ConfigDict(from_attributes=True,
                              alias_generator=camel,
                              populate_by_name=True)