import { AppHeader } from "@/components/layout/AppHeader";
import { KPICard } from "@/components/dashboard/KPICard";
import { ActivityItem } from "@/components/dashboard/ActivityItem";
import { Panel } from "@/components/common/Panel";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { Button } from "@/components/ui/button";
import { FileSpreadsheet, Clock, ShieldCheck, FilePlus2, AlertTriangle, ArrowRight, Plus } from "lucide-react";
import { Link } from "react-router-dom";

const recentActivity = [
  {
    tagNumber: "20-LCV-3045",
    description: "Level Control Valve - Separator V-2001",
    status: "approved" as const,
    timestamp: "2h ago",
    user: "M. Chen",
  },
  {
    tagNumber: "20-PCV-3102",
    description: "Pressure Control Valve - Gas Compression",
    status: "generated" as const,
    timestamp: "4h ago",
    user: "J. Morrison",
  },
  {
    tagNumber: "20-XV-3088",
    description: "Shutdown Valve - Emergency Depressurization",
    status: "pending" as const,
    timestamp: "6h ago",
    user: "S. Patel",
  },
  {
    tagNumber: "20-FCV-3201",
    description: "Flow Control Valve - Water Injection",
    status: "conflict" as const,
    timestamp: "8h ago",
    user: "R. Kumar",
  },
  {
    tagNumber: "20-HCV-3015",
    description: "Hand Control Valve - Chemical Injection",
    status: "draft" as const,
    timestamp: "1d ago",
    user: "J. Morrison",
  },
];

const projectSummary = [
  { line: "Separation System", total: 45, generated: 38, approved: 32 },
  { line: "Gas Compression", total: 28, generated: 25, approved: 20 },
  { line: "Water Injection", total: 18, generated: 12, approved: 8 },
  { line: "Chemical Injection", total: 15, generated: 15, approved: 15 },
];

export default function Dashboard() {
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <AppHeader title="Dashboard" breadcrumbs={[{ label: "FPSO Prosperity" }]} />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6 animate-fade-in">
          {/* KPI Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <KPICard
              title="Datasheets Generated"
              value="156"
              subtitle="This month"
              icon={FileSpreadsheet}
              trend={{ value: 23, direction: "up", label: "vs last month" }}
              variant="primary"
            />
            <KPICard
              title="Engineering Hours Saved"
              value="432"
              subtitle="Estimated total"
              icon={Clock}
              trend={{ value: 18, direction: "up", label: "efficiency gain" }}
              variant="accent"
            />
            <KPICard
              title="Approvel Pending"
              value="16"
              subtitle="This month"
              icon={FileSpreadsheet}
              trend={{ value: 23, direction: "up", label: "vs last month" }}
              variant="primary"
            />
            {/* <KPICard
              title="Errors Prevented"
              value="89"
              subtitle="Data conflicts caught"
              icon={AlertTriangle}
              trend={{ value: 12, direction: "down", label: "error rate" }}
              variant="assumption"
            /> */}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Recent Activity */}
            <Panel
              title="Recent Activity"
              description="Latest datasheet updates"
              className="lg:col-span-2"
              actions={
                <Link to="/automation">
                  <Button variant="ghost" size="sm" className="gap-1.5">
                    View All <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </Link>
              }
            >
              <div className="divide-y divide-border">
                {recentActivity.map((item) => (
                  <ActivityItem key={item.tagNumber} {...item} />
                ))}
              </div>
            </Panel>

            {/* Quick Actions */}
            <div className="space-y-6">
              <Panel title="Quick Actions">
                <div className="space-y-2">
                  <Link to="/generator" className="block">
                    <Button className="w-full justify-start gap-2 bg-accent hover:bg-accent/90" size="lg">
                      <FilePlus2 className="w-4 h-4" />
                      Valve Datasheet Generator
                    </Button>
                  </Link>
                  {/* <Link to="/automation" className="block">
                    <Button className="w-full justify-start gap-2" size="lg">
                      <Plus className="w-4 h-4" />
                      New Valve Datasheet
                    </Button>
                  </Link> */}
                  <Link to="/validation" className="block">
                    <Button variant="outline" className="w-full justify-start gap-2" size="lg">
                      <ShieldCheck className="w-4 h-4" />
                      Review Validations
                    </Button>
                  </Link>
                  <Link to="/approval" className="block">
                    <Button variant="outline" className="w-full justify-start gap-2" size="lg">
                      <FileSpreadsheet className="w-4 h-4" />
                      Pending Approvals
                    </Button>
                  </Link>
                </div>
              </Panel>

              <Panel title="Project Progress" description="FPSO Prosperity - Valve Datasheets">
                <div className="space-y-3">
                  {projectSummary.map((item) => (
                    <div key={item.line} className="space-y-1.5">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-foreground font-medium">{item.line}</span>
                        <span className="text-muted-foreground">
                          {item.approved}/{item.total}
                        </span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-validated rounded-full transition-all"
                          style={{
                            width: `${(item.approved / item.total) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
            </div>
          </div>

          {/* Project Summary Table */}
          {/* <Panel title="System Overview" description="Datasheet status by system">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="data-table-header">
                    <th className="px-4 py-3 text-left">System</th>
                    <th className="px-4 py-3 text-center">Total</th>
                    <th className="px-4 py-3 text-center">Draft</th>
                    <th className="px-4 py-3 text-center">Generated</th>
                    <th className="px-4 py-3 text-center">Approved</th>
                    <th className="px-4 py-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {projectSummary.map((item, idx) => (
                    <tr key={item.line} className="data-table-row">
                      <td className="px-4 py-3 font-medium">{item.line}</td>
                      <td className="px-4 py-3 text-center font-mono">{item.total}</td>
                      <td className="px-4 py-3 text-center font-mono text-muted-foreground">
                        {item.total - item.generated}
                      </td>
                      <td className="px-4 py-3 text-center font-mono text-primary">{item.generated - item.approved}</td>
                      <td className="px-4 py-3 text-center font-mono text-validated">{item.approved}</td>
                      <td className="px-4 py-3 text-center">
                        <StatusBadge
                          status={
                            item.approved === item.total
                              ? "approved"
                              : item.generated > item.approved
                                ? "pending"
                                : "generated"
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel> */}
        </div>
      </div>
    </div>
  );
}
