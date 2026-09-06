"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { apiService } from "../../../services/api";
import { CargoType, ShipmentPriority } from "../../../types/api";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Alert, AlertDescription } from "../../../components/ui/alert";

export default function NewShipmentPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    origin: "",
    destination: "",
    cargo_type: "GENERAL" as CargoType,
    weight: "",
    shipment_value: "",
    delivery_deadline: "",
    priority: "STANDARD" as ShipmentPriority,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      // Validate and cast inputs
      const weight = parseFloat(formData.weight);
      const value = parseFloat(formData.shipment_value);

      if (isNaN(weight) || weight <= 0) throw new Error("Invalid weight");
      if (isNaN(value) || value < 0) throw new Error("Invalid shipment value");
      if (!formData.delivery_deadline) throw new Error("Delivery deadline is required");
      
      const payload = {
        origin: formData.origin,
        destination: formData.destination,
        cargo_type: formData.cargo_type,
        weight: weight,
        shipment_value: value,
        delivery_deadline: new Date(formData.delivery_deadline).toISOString(),
        priority: formData.priority,
      };

      const shipment = await apiService.createShipment(payload);
      router.push(`/shipments/${shipment.id}`);
      router.refresh(); // Invalidate Next.js cache so the list updates
    } catch (err: any) {
      setError(err.message || "Failed to create shipment");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/shipments">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Create Shipment</h1>
          <p className="text-gray-500 mt-1">Enter the details for your new shipment request.</p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Shipment Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="origin">Origin</label>
                <Input
                  id="origin"
                  name="origin"
                  required
                  placeholder="e.g. Shanghai"
                  value={formData.origin}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="destination">Destination</label>
                <Input
                  id="destination"
                  name="destination"
                  required
                  placeholder="e.g. Rotterdam"
                  value={formData.destination}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="cargo_type">Cargo Type</label>
                <select
                  id="cargo_type"
                  name="cargo_type"
                  className="flex h-9 w-full rounded-md border border-gray-200 bg-transparent px-3 py-1 text-sm shadow-sm"
                  value={formData.cargo_type}
                  onChange={handleChange}
                >
                  <option value="GENERAL">General</option>
                  <option value="PERISHABLE">Perishable</option>
                  <option value="HAZARDOUS">Hazardous</option>
                  <option value="FRAGILE">Fragile</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="priority">Priority</label>
                <select
                  id="priority"
                  name="priority"
                  className="flex h-9 w-full rounded-md border border-gray-200 bg-transparent px-3 py-1 text-sm shadow-sm"
                  value={formData.priority}
                  onChange={handleChange}
                >
                  <option value="STANDARD">Standard</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="weight">Weight (kg)</label>
                <Input
                  id="weight"
                  name="weight"
                  type="number"
                  min="0.1"
                  step="0.1"
                  required
                  value={formData.weight}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="shipment_value">Value ($)</label>
                <Input
                  id="shipment_value"
                  name="shipment_value"
                  type="number"
                  min="0"
                  step="0.01"
                  required
                  value={formData.shipment_value}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="delivery_deadline">Deadline</label>
                <Input
                  id="delivery_deadline"
                  name="delivery_deadline"
                  type="datetime-local"
                  required
                  value={formData.delivery_deadline}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create Shipment
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
