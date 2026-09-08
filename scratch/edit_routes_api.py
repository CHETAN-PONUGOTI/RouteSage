import re

with open('backend/app/api/routers/routes.py', 'r') as f:
    content = f.read()

additions = """
@router.put("/{shipment_id}/routes/{route_id}", response_model=RouteResponse)
def update_route(shipment_id: UUID, route_id: UUID, data: RouteCreate, service: OptimizationService = Depends(get_optimization_service)):
    return service.update_route(shipment_id, route_id, data)

@router.delete("/{shipment_id}/routes/{route_id}", status_code=204)
def delete_route(shipment_id: UUID, route_id: UUID, service: OptimizationService = Depends(get_optimization_service)):
    service.delete_route(shipment_id, route_id)
"""

content += additions

with open('backend/app/api/routers/routes.py', 'w') as f:
    f.write(content)
