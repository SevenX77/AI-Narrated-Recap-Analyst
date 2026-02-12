import * as React from "react"
import { cn } from "@/lib/utils"

interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg"
}

const Spinner = React.forwardRef<HTMLDivElement, SpinnerProps>(
  ({ className, size = "md", ...props }, ref) => {
    const sizeClasses = {
      sm: "w-4 h-4 border-2",
      md: "w-6 h-6 border-2",
      lg: "w-8 h-8 border-3",
    }

    return (
      <div
        ref={ref}
        className={cn("flex items-center justify-center", className)}
        {...props}
      >
        <div
          className={cn(
            "animate-spin rounded-full border-solid border-primary border-t-transparent",
            sizeClasses[size]
          )}
        />
      </div>
    )
  }
)
Spinner.displayName = "Spinner"

export { Spinner }
