import { AlertCircle, RefreshCcw } from "lucide-react"
import { Button } from "./button"

export function ErrorState({ 
  title = "Something went wrong", 
  message = "An error occurred while loading this data.",
  onRetry
}: { 
  title?: string
  message?: string
  onRetry?: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-4 min-h-[200px] border rounded-lg bg-red-50/30">
      <div className="bg-white p-3 rounded-full border border-red-100 shadow-sm">
        <AlertCircle className="h-6 w-6 text-red-500" />
      </div>
      <div className="text-center">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500 mt-1 max-w-md">{message}</p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-2">
          <RefreshCcw className="mr-2 h-4 w-4" />
          Try Again
        </Button>
      )}
    </div>
  )
}
