from pydantic import BaseModel


class AdminOverviewResponse(BaseModel):
    clients_total: int
    clients_active: int
    clients_suspended: int
    clients_created_this_month: int
