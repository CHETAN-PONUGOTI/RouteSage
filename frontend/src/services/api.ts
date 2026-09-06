import { apiClient } from '../lib/api-client';
import { Shipment, Route, OptimizationResult, OptimizationProfile } from '../types/api';

export const apiService = {
  // Shipments
  getShipments: () => apiClient.get<Shipment[]>('/api/v1/shipments'),
  getShipment: (id: string) => apiClient.get<Shipment>(`/api/v1/shipments/${id}`),
  createShipment: (data: Omit<Shipment, 'id' | 'created_at' | 'updated_at'>) => 
    apiClient.post<Shipment>('/api/v1/shipments', data),

  // Routes
  getRoutes: (shipmentId: string) => apiClient.get<Route[]>(`/api/v1/shipments/${shipmentId}/routes`),
  createRoutes: (shipmentId: string, routes: any[]) => 
    apiClient.post<Route[]>(`/api/v1/shipments/${shipmentId}/routes`, routes),

  // Optimization
  runOptimization: (shipmentId: string, profile: OptimizationProfile) => 
    apiClient.post<OptimizationResult>(`/api/v1/shipments/${shipmentId}/optimize`, { profile }),
  getOptimizationRun: (runId: string) => apiClient.get<OptimizationResult>(`/api/v1/optimization-runs/${runId}`)
};
