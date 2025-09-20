from pydantic import BaseModel, Field, ConfigDict

def to_camel(s: str) -> str:
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])

class BaseDTO(BaseModel):
    # 允许 camelCase 入参；导出时默认 snake_case
    model_config = ConfigDict(
        alias_generator=to_camel,   # 自动把 snake 名 -> camel 别名
        populate_by_name=True       # 入参既可 camel 也可 snake
    )