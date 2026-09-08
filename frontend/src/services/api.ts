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
  updateRoute: (shipmentId: string, routeId: string, data: any) =>
    apiClient.put<Route>(`/api/v1/shipments/${shipmentId}/routes/${routeId}`, data),
  deleteRoute: (shipmentId: string, routeId: string) =>
    apiClient.delete<void>(`/api/v1/shipments/${shipmentId}/routes/${routeId}`),

  // Optimization
  runOptimization: (shipmentId: string, profile: OptimizationProfile) => 
    apiClient.post<OptimizationResult>(`/api/v1/shipments/${shipmentId}/optimize`, { profile }),
  getOptimizationRun: (runId: string) => 
    apiClient.get<OptimizationResult>(`/api/v1/optimization-runs/${runId}`),
  getExplanation: (runId: string) =>
    apiClient.post<{ explanation: string; generated_by: string; run_id: string }>(`/api/v1/optimization-runs/${runId}/explanation`, {}),

  // System
  checkHealth: () => apiClient.get<{ status: string }>('/health'),
};
