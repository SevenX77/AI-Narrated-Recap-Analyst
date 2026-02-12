import * as React from "react"
import { Upload, X, File } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./button"
import { ScrollArea } from "./scroll-area"

export interface FileUploadProps {
  accept?: string
  multiple?: boolean
  maxSize?: number // in bytes
  value?: File[] // 受控组件的值
  onFilesChange?: (files: File[]) => void
  className?: string
}

export function FileUpload({
  accept,
  multiple = false,
  maxSize = 50 * 1024 * 1024, // 50MB default
  value,
  onFilesChange,
  className,
}: FileUploadProps) {
  const [internalFiles, setInternalFiles] = React.useState<File[]>([])
  const [isDragging, setIsDragging] = React.useState(false)
  const inputRef = React.useRef<HTMLInputElement>(null)
  
  // 使用受控模式或非受控模式
  const files = value !== undefined ? value : internalFiles

  const handleFiles = (newFiles: FileList | null) => {
    if (!newFiles) return

    const validFiles: File[] = []
    Array.from(newFiles).forEach((file) => {
      if (file.size > maxSize) {
        alert(`File ${file.name} is too large. Max size is ${maxSize / 1024 / 1024}MB`)
        return
      }
      validFiles.push(file)
    })

    const updatedFiles = multiple ? [...files, ...validFiles] : validFiles
    
    // 如果是受控组件，只调用回调；否则更新内部状态
    if (value !== undefined) {
      onFilesChange?.(updatedFiles)
    } else {
      setInternalFiles(updatedFiles)
      onFilesChange?.(updatedFiles)
    }
  }

  const removeFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index)
    
    // 如果是受控组件，只调用回调；否则更新内部状态
    if (value !== undefined) {
      onFilesChange?.(updatedFiles)
    } else {
      setInternalFiles(updatedFiles)
      onFilesChange?.(updatedFiles)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer transition-colors",
          isDragging
            ? "border-primary bg-primary/10"
            : "border-border bg-background hover:bg-accent hover:border-primary/50"
        )}
      >
        <Upload className="h-8 w-8 text-muted-foreground mb-2" />
        <p className="text-sm font-mono text-muted-foreground">
          Click to upload or drag and drop
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {accept || "All file types"} • Max {maxSize / 1024 / 1024}MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <ScrollArea className="max-h-[300px] overflow-hidden">
          <div className="space-y-2 pr-4">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-md border border-border bg-card"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <File className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-mono truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeFile(index)}
                  className="shrink-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  )
}
