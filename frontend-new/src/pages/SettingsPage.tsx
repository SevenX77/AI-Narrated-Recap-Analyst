import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Cloud, Palette, Bell, Save, RotateCcw } from "lucide-react"

export default function SettingsPage() {
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        {/* Header */}
        <div className="px-4 lg:px-6">
          <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
          <p className="text-muted-foreground mt-1">
            Configure your application preferences
          </p>
        </div>

        <div className="px-4 lg:px-6">
          <Separator className="mb-6" />
        </div>

        <div className="px-4 lg:px-6 space-y-6 max-w-4xl">
          {/* API Settings */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Cloud className="h-5 w-5 text-primary" />
                <div>
                  <CardTitle>API Configuration</CardTitle>
                  <CardDescription className="mt-1.5">
                    Configure backend API and LLM provider settings
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="api-url">API Base URL</Label>
                <Input
                  id="api-url"
                  placeholder="http://localhost:8000"
                  defaultValue="http://localhost:8000"
                />
                <p className="text-xs text-muted-foreground">
                  The backend API endpoint for all requests
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="llm-provider">LLM Provider</Label>
                <Select defaultValue="claude">
                  <SelectTrigger id="llm-provider">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="claude">Claude (Anthropic)</SelectItem>
                    <SelectItem value="openai">OpenAI GPT-4</SelectItem>
                    <SelectItem value="deepseek">DeepSeek</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Select your preferred AI model provider
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Appearance */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Palette className="h-5 w-5 text-primary" />
                <div>
                  <CardTitle>Appearance</CardTitle>
                  <CardDescription className="mt-1.5">
                    Customize the visual theme of the application
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="theme">Theme Mode</Label>
                <Select defaultValue="dark">
                  <SelectTrigger id="theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="system">System Default</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Choose your preferred color scheme
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" />
                <div>
                  <CardTitle>Notifications</CardTitle>
                  <CardDescription className="mt-1.5">
                    Manage workflow and system notifications
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg border border-dashed p-8 text-center">
                <Bell className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">
                  Notification preferences will be available soon
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" className="gap-2">
              <RotateCcw className="h-4 w-4" />
              Reset to Defaults
            </Button>
            <Button className="gap-2">
              <Save className="h-4 w-4" />
              Save Changes
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
