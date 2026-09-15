from app.schemas.camel import CamelModel


class AdoSuggestionResponse(CamelModel):
    ado_work_item_id: int
    title: str
    type: str


class AdoReferenceResponse(CamelModel):
    ado_work_item_id: int
    title: str | None
    type: str | None
    is_available: bool
    open_url: str | None
