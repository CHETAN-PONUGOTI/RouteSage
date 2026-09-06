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
          <h1 className="text-3xl font-bold tracking-tight">Shipments</h1>
          <p className="text-gray-500 mt-1">Manage and track your active shipments.</p>
        </div>
        <Link href="/shipments/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Shipment
          </Button>
        </Link>
      </div>

      {shipments.length === 0 ? (
        <EmptyState 
          title="No shipments found" 
          description="You haven't created any shipments yet. Get started by creating a new shipment."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {shipments.map((shipment) => (
            <Link key={shipment.id} href={`/shipments/${shipment.id}`} className="block">
              <Card className="hover:border-blue-300 transition-colors cursor-pointer h-full">
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-lg truncate" title={`${shipment.origin} to ${shipment.destination}`}>
                      {shipment.origin} → {shipment.destination}
                    </CardTitle>
                    <Badge variant="secondary" className="text-[10px]">
                      {shipment.priority}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-gray-500 space-y-1">
                    <div className="flex justify-between">
                      <span>Cargo Type:</span>
                      <span className="font-medium text-gray-900">{shipment.cargo_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Weight:</span>
                      <span className="font-medium text-gray-900">{shipment.weight} kg</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Deadline:</span>
                      <span className="font-medium text-gray-900">
                        {new Date(shipment.delivery_deadline).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
