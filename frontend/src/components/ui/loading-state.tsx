import { Loader2 } from "lucide-react"

export function LoadingState({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-4 min-h-[200px]">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      <p className="text-sm font-medium text-gray-700">{message}</p>
    </div>
  )
}
