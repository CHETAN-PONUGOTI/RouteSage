"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Package, Clock, Scale, DollarSign, Activity } from "lucide-react";
import { apiService } from "../../../services/api";
import { Shipment, Route } from "../../../types/api";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Badge } from "../../../components/ui/badge";
import { LoadingState } from "../../../components/ui/loading-state";
import { ErrorState } from "../../../components/ui/error-state";
import { Alert, AlertDescription } from "../../../components/ui/alert";

export default function ShipmentDetailPage() {
  const params = useParams();
  const shipmentId = params.shipmentId as string;
  const router = useRouter();

  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetails = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const shipmentData = await apiService.getShipment(shipmentId);
      setShipment(shipmentData);

      try {
        const routeData = await apiService.getRoutes(shipmentId);
        setRoutes(routeData);
      } catch (err: any) {
        // If 404 on routes or other error, handle it gracefully. We just might not have routes yet.
        setRoutes([]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load shipment details");
    } finally {
      setLoading(false);
    }
  }, [shipmentId]);

  useEffect(() => {
    if (shipmentId) {
      fetchDetails();
    }
  }, [shipmentId, fetchDetails]);

  if (loading) return <LoadingState message="Loading shipment details..." />;
  if (error) return <ErrorState message={error} onRetry={fetchDetails} />;
  if (!shipment) return <ErrorState title="Not Found" message="Shipment could not be found." />;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/shipments">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {shipment.origin} → {shipment.destination}
          </h1>
          <p className="text-gray-500 mt-1 font-mono text-sm">ID: {shipment.id}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Shipment Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-2 border-b">
              <span className="flex items-center text-sm font-medium text-gray-500">
                <Package className="mr-2 h-4 w-4" /> Cargo Type
              </span>
              <Badge variant="outline">{shipment.cargo_type}</Badge>
            </div>
            <div className="flex items-center justify-between py-2 border-b">
              <span className="flex items-center text-sm font-medium text-gray-500">
                <Activity className="mr-2 h-4 w-4" /> Priority
              </span>
              <Badge>{shipment.priority}</Badge>
            </div>
            <div className="flex items-center justify-between py-2 border-b">
              <span className="flex items-center text-sm font-medium text-gray-500">
                <Scale className="mr-2 h-4 w-4" /> Weight
              </span>
              <span className="font-semibold">{shipment.weight.toLocaleString()} kg</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b">
              <span className="flex items-center text-sm font-medium text-gray-500">
                <DollarSign className="mr-2 h-4 w-4" /> Value
              </span>
              <span className="font-semibold">${shipment.shipment_value.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="flex items-center text-sm font-medium text-gray-500">
                <Clock className="mr-2 h-4 w-4" /> Deadline
              </span>
              <span className="font-semibold">{new Date(shipment.delivery_deadline).toLocaleString()}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Route Availability</CardTitle>
          </CardHeader>
          <CardContent>
            {routes.length > 0 ? (
              <div className="space-y-6">
                <div className="flex items-center justify-center p-6 bg-blue-50 border border-blue-100 rounded-lg">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-blue-600">{routes.length}</div>
                    <div className="text-sm font-medium text-blue-800 mt-1">Candidate Routes Available</div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold">Available Candidates:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {routes.map((r) => (
                      <li key={r.id} className="flex justify-between items-center bg-gray-50 px-3 py-2 rounded">
                        <span className="truncate mr-4">{r.route_name}</span>
                        <span className="font-mono text-xs">{r.legs.length} leg(s)</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Phase 12 CTA */}
                <Link href={`/shipments/${shipmentId}/evaluate`}>
                  <Button className="w-full" size="lg">
                    Evaluate Routes
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                <Alert>
                  <AlertDescription>
                    No candidate routes have been generated for this shipment yet.
                  </AlertDescription>
                </Alert>
                <div className="text-sm text-gray-500 text-center py-4 border border-dashed rounded bg-gray-50">
                  <p>Route generation integration is pending.</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
