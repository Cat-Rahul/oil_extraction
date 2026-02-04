import { useState } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { Panel } from "@/components/common/Panel";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  GitCompare,
  Download,
  FileSpreadsheet,
  Check,
  X,
  Clock,
  User,
  ChevronRight,
  MessageSquare,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const versions = [
  {
    version: "v3",
    status: "current",
    date: "2024-01-15 16:20",
    author: "J. Morrison",
    changes: "Confirmed 4\" size per sizing calculation",
  },
  {
    version: "v2",
    status: "superseded",
    date: "2024-01-15 14:32",
    author: "System",
    changes: "Auto-generated from PMS data",
  },
  {
    version: "v1",
    status: "superseded",
    date: "2024-01-14 09:15",
    author: "System",
    changes: "Initial draft generation",
  },
];

const pendingApprovals = [
  {
    tag: "20-PCV-3102",
    description: "Pressure Control Valve - Gas Compression",
    submittedBy: "J. Morrison",
    submittedAt: "2h ago",
    status: "pending",
    reviewers: ["M. Chen", "S. Patel"],
  },
  {
    tag: "20-LCV-3045",
    description: "Level Control Valve - Separator V-2001",
    submittedBy: "R. Kumar",
    submittedAt: "4h ago",
    status: "approved",
    reviewers: ["M. Chen"],
  },
  {
    tag: "20-XV-3088",
    description: "Shutdown Valve - Emergency Depressurization",
    submittedBy: "S. Patel",
    submittedAt: "1d ago",
    status: "pending",
    reviewers: ["J. Morrison", "M. Chen"],
  },
];

const reviewComments = [
  {
    reviewer: "M. Chen",
    role: "Lead Mechanical Engineer",
    date: "2024-01-15 15:45",
    comment: "Please verify the size reduction with process team before final approval.",
    status: "open",
  },
  {
    reviewer: "J. Morrison",
    role: "Lead Process Engineer",
    date: "2024-01-15 16:18",
    comment: "Size reduction confirmed per sizing calculation SC-3102-001. Reduced bore is intentional for better control.",
    status: "resolved",
  },
];

export default function ApprovalPage() {
  const [reviewComment, setReviewComment] = useState("");
  const { toast } = useToast();

  const handleApprove = () => {
    toast({
      title: "Datasheet Approved",
      description: "20-PCV-3102 has been approved and is ready for issue",
    });
  };

  const handleReject = () => {
    toast({
      title: "Datasheet Returned",
      description: "20-PCV-3102 has been returned for revision",
      variant: "destructive",
    });
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <AppHeader
        title="Approval & Version Control"
        breadcrumbs={[
          { label: "FPSO Prosperity", href: "/" },
          { label: "Approval & Versions" },
        ]}
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6 animate-fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Pending Approvals */}
            <div className="lg:col-span-2">
              <Panel
                title="Pending Approvals"
                description="Datasheets awaiting review"
              >
                <div className="space-y-3">
                  {pendingApprovals.map((item) => (
                    <div
                      key={item.tag}
                      className="flex items-center justify-between p-4 border border-border rounded-lg hover:border-primary/30 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-sm font-medium">
                            {item.tag}
                          </span>
                          <StatusBadge
                            status={item.status as "pending" | "approved"}
                          />
                        </div>
                        <p className="text-sm text-muted-foreground mt-0.5">
                          {item.description}
                        </p>
                        <div className="flex items-center gap-4 mt-2">
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <User className="w-3 h-3" />
                            {item.submittedBy}
                          </div>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Clock className="w-3 h-3" />
                            {item.submittedAt}
                          </div>
                        </div>
                      </div>
                      {item.status === "pending" ? (
                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm">
                            Review
                            <ChevronRight className="w-4 h-4 ml-1" />
                          </Button>
                        </div>
                      ) : (
                        <Badge className="bg-validated-bg text-validated border-0">
                          <Check className="w-3 h-3 mr-1" />
                          Approved
                        </Badge>
                      )}
                    </div>
                  ))}
                </div>
              </Panel>

              {/* Review Panel */}
              <div className="mt-6">
                <Panel
                  title="Review: 20-PCV-3102"
                  description="Pressure Control Valve - Gas Compression"
                  actions={
                    <div className="flex items-center gap-2">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm" className="gap-1.5">
                            <GitCompare className="w-4 h-4" />
                            Compare Versions
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-3xl">
                          <DialogHeader>
                            <DialogTitle>Version Comparison</DialogTitle>
                            <DialogDescription>
                              Compare changes between datasheet versions
                            </DialogDescription>
                          </DialogHeader>
                          <div className="grid grid-cols-2 gap-4 py-4">
                            <div className="space-y-2">
                              <Select defaultValue="v2">
                                <SelectTrigger>
                                  <SelectValue placeholder="Select version" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="v2">v2 - System (Auto)</SelectItem>
                                  <SelectItem value="v1">v1 - Initial Draft</SelectItem>
                                </SelectContent>
                              </Select>
                              <div className="p-4 bg-muted rounded-lg">
                                <p className="text-sm font-mono">Size: 6"</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                  Original from line size
                                </p>
                              </div>
                            </div>
                            <div className="space-y-2">
                              <Select defaultValue="v3">
                                <SelectTrigger>
                                  <SelectValue placeholder="Select version" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="v3">v3 - Current</SelectItem>
                                  <SelectItem value="v2">v2 - System (Auto)</SelectItem>
                                </SelectContent>
                              </Select>
                              <div className="p-4 bg-validated-bg rounded-lg border border-validated/20">
                                <p className="text-sm font-mono">Size: 4"</p>
                                <p className="text-xs text-validated mt-1">
                                  Changed per sizing calculation
                                </p>
                              </div>
                            </div>
                          </div>
                        </DialogContent>
                      </Dialog>
                    </div>
                  }
                >
                  {/* Review Comments */}
                  <div className="space-y-4 mb-6">
                    <h4 className="text-sm font-medium flex items-center gap-2">
                      <MessageSquare className="w-4 h-4" />
                      Review Comments
                    </h4>
                    {reviewComments.map((comment, idx) => (
                      <div
                        key={idx}
                        className={`p-4 rounded-lg border ${
                          comment.status === "open"
                            ? "bg-assumption-bg border-assumption/20"
                            : "bg-muted/30 border-border"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm">
                              {comment.reviewer}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {comment.role}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant="secondary"
                              className={
                                comment.status === "open"
                                  ? "bg-assumption-bg text-assumption-foreground"
                                  : "bg-validated-bg text-validated"
                              }
                            >
                              {comment.status === "open" ? "Open" : "Resolved"}
                            </Badge>
                            <span className="text-[10px] text-muted-foreground">
                              {comment.date}
                            </span>
                          </div>
                        </div>
                        <p className="text-sm text-foreground">{comment.comment}</p>
                      </div>
                    ))}

                    {/* Add Comment */}
                    <div className="space-y-2">
                      <Textarea
                        placeholder="Add review comment..."
                        value={reviewComment}
                        onChange={(e) => setReviewComment(e.target.value)}
                      />
                      <Button variant="outline" size="sm">
                        Add Comment
                      </Button>
                    </div>
                  </div>

                  {/* Approval Actions */}
                  <div className="flex items-center gap-3 pt-4 border-t border-border">
                    <Button
                      className="flex-1 gap-2 bg-validated hover:bg-validated/90"
                      onClick={handleApprove}
                    >
                      <Check className="w-4 h-4" />
                      Approve
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1 gap-2 border-conflict text-conflict hover:bg-conflict/10"
                      onClick={handleReject}
                    >
                      <X className="w-4 h-4" />
                      Return for Revision
                    </Button>
                  </div>
                </Panel>
              </div>
            </div>

            {/* Version History & Export */}
            <div className="space-y-6">
              <Panel title="Version History">
                <div className="space-y-3">
                  {versions.map((version) => (
                    <div
                      key={version.version}
                      className={`p-3 rounded-lg border ${
                        version.status === "current"
                          ? "border-primary bg-primary/5"
                          : "border-border"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono font-medium">
                          {version.version}
                        </span>
                        {version.status === "current" && (
                          <Badge className="bg-primary text-primary-foreground">
                            Current
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {version.changes}
                      </p>
                      <div className="flex items-center gap-2 mt-2 text-[10px] text-muted-foreground">
                        <User className="w-3 h-3" />
                        {version.author}
                        <span>•</span>
                        {version.date}
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel title="Export Options">
                <div className="space-y-2">
                  <Button variant="outline" className="w-full justify-start gap-2">
                    <FileSpreadsheet className="w-4 h-4" />
                    Export to Excel
                  </Button>
                  <Button variant="outline" className="w-full justify-start gap-2">
                    <Download className="w-4 h-4" />
                    Export to PDF
                  </Button>
                </div>
              </Panel>

              <Panel title="Assigned Reviewers">
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">M. Chen</p>
                        <p className="text-[10px] text-muted-foreground">
                          Lead Mechanical Engineer
                        </p>
                      </div>
                    </div>
                    <Badge variant="secondary">Pending</Badge>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-muted/30 rounded">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">S. Patel</p>
                        <p className="text-[10px] text-muted-foreground">
                          Engineering Manager
                        </p>
                      </div>
                    </div>
                    <Badge variant="secondary">Pending</Badge>
                  </div>
                </div>
              </Panel>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
