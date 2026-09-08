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
          <Button variant="outline" size="icon" className="border-gray-300">
            <ArrowLeft className="h-5 w-5 text-gray-700" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">
            {shipment.origin} â†’ {shipment.destination}
          </h1>
          <p className="text-gray-600 mt-1 font-mono text-sm">Shipment ID: {shipment.id}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="border-b border-gray-100 pb-3">
            <CardTitle className="text-lg font-bold text-gray-900">Shipment Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="flex items-center text-sm font-semibold text-gray-700">
                <Package className="mr-2 h-4 w-4 text-gray-500" /> Cargo Type
              </span>
              <Badge variant="outline" className="border-gray-300 text-gray-900 font-bold">{shipment.cargo_type}</Badge>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="flex items-center text-sm font-semibold text-gray-700">
                <Activity className="mr-2 h-4 w-4 text-gray-500" /> Priority
              </span>
              <Badge variant={shipment.priority === "URGENT" ? "destructive" : "secondary"} className="font-bold">
                {shipment.priority}
              </Badge>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="flex items-center text-sm font-semibold text-gray-700">
                <Scale className="mr-2 h-4 w-4 text-gray-500" /> Weight
              </span>
              <span className="font-bold text-gray-900">{shipment.weight.toLocaleString()} kg</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="flex items-center text-sm font-semibold text-gray-700">
                <DollarSign className="mr-2 h-4 w-4 text-gray-500" /> Value
              </span>
              <span className="font-bold text-gray-900">${shipment.shipment_value.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="flex items-center text-sm font-semibold text-gray-700">
                <Clock className="mr-2 h-4 w-4 text-gray-500" /> Deadline
              </span>
              <span className="font-bold text-gray-900">{new Date(shipment.delivery_deadline).toLocaleString()}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b border-gray-100 pb-3">
            <CardTitle className="text-lg font-bold text-gray-900">Route Availability</CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            {routes.length > 0 ? (
              <div className="space-y-6">
                <div className="flex items-center justify-center p-6 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="text-center">
                    <div className="text-4xl font-extrabold text-blue-700">{routes.length}</div>
                    <div className="text-sm font-bold text-blue-900 mt-1">Candidate Routes Available</div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h4 className="text-sm font-bold text-gray-900">Available Corridors:</h4>
                  <ul className="text-sm space-y-1.5">
                    {routes.map((r) => (
                      <li key={r.id} className="flex justify-between items-center bg-gray-50 border border-gray-200 px-3 py-2 rounded text-gray-900 font-medium">
                        <span className="truncate mr-4 text-gray-900">{r.route_name}</span>
                        <span className="font-mono text-xs text-gray-600 bg-white border border-gray-200 px-1.5 py-0.5 rounded">{r.legs.length} leg(s)</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <Link href={`/shipments/${shipmentId}/evaluate`} className="block">
                  <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold shadow-sm" size="lg">
                    Evaluate Routes Under Constraints
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
