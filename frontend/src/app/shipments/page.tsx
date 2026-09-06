"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { apiService } from "../../services/api";
import { Shipment } from "../../types/api";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { LoadingState } from "../../components/ui/loading-state";
import { ErrorState } from "../../components/ui/error-state";
import { EmptyState } from "../../components/ui/empty-state";

export default function ShipmentsPage() {
  const [shipments, setShipments] = 
    useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchShipments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getShipments();
      setShipments(data);
    } catch (err: any) {
      setError(err.message || "Failed to load shipments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShipments();
  }, []);

  if (loading) {
    return <LoadingState message="Loading shipments..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchShipments} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">Shipments</h1>
          <p className="text-gray-600 mt-1 text-sm">Manage and evaluate multi-modal logistics shipments.</p>
        </div>
        <Link href="/shipments/new">
          <Button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm">
            <Plus className="mr-2 h-4 w-4" />
            New Shipment
          </Button>
        </Link>
      </div>

      {shipments.length === 0 ? (
        <EmptyState 
          title="No shipments found" 
          description="No active shipments found. Run the seed script or create a new shipment."
        />
      ) : (
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {shipments.map((shipment) => (
            <div key={shipment.id} className="block">
              <Card className="hover:border-blue-400 hover:shadow-md transition-all h-full flex flex-col justify-between">
                <CardHeader className="pb-3 border-b border-gray-100">
                  <div className="flex justify-between items-start gap-2">
                    <CardTitle className="text-base font-bold text-gray-900 truncate" title={`${shipment.origin} to ${shipment.destination}`}>
                      {shipment.origin} → {shipment.destination}
                    </CardTitle>
                    <Badge 
                      variant={shipment.priority === "URGENT" ? "destructive" : "secondary"} 
                      className="text-[10px] font-bold uppercase tracking-wider shrink-0"
                    >
                      {shipment.priority}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-3 flex-1 flex flex-col justify-between">
                  <div className="text-xs text-gray-600 space-y-1.5 mb-4">
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-500">Cargo Type:</span>
                      <span className="font-semibold text-gray-900">{shipment.cargo_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-500">Weight:</span>
                      <span className="font-semibold text-gray-900">{shipment.weight != null ? shipment.weight.toLocaleString() : 0} kg</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-500">Value:</span>
                      <span className="font-semibold text-gray-900">${shipment.shipment_value != null ? shipment.shipment_value.toLocaleString() : "0"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-500">Deadline:</span>
                      <span className="font-semibold text-gray-900">{shipment.delivery_deadline ? new Date(shipment.delivery_deadline).toLocaleDateString() : "-"}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
                    <Link href={`/shipments/${shipment.id}`} className="flex-1">
                      <Button variant="outline" size="sm" className="w-full text-xs font-semibold text-gray-700 hover:text-gray-900 border-gray-300">
                        Details
                      </Button>
                    </Link>
                    <Link href={`/shipments/${shipment.id}/evaluate`} className="flex-1">
                      <Button size="sm" className="w-full text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm">
                        Evaluate
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
