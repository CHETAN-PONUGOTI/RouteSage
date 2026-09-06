import { FileBox } from "lucide-react"

export function EmptyState({ 
  title = "No data found", 
  description = "Get started by creating a new record."
}: { 
  title?: string
  description?: string 
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-3 min-h-[200px] border border-dashed border-gray-300 rounded-lg bg-gray-50">
      <div className="bg-white p-3 rounded-full border border-gray-200 shadow-sm">
        <FileBox className="h-6 w-6 text-gray-500" />
      </div>
      <div className="text-center">
        <h3 className="font-bold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-600 mt-1">{description}</p>
      </div>
    </div>
  )
}
