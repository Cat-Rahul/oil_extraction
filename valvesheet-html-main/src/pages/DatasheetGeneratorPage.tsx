import { useState, useEffect, useCallback } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  FileSpreadsheet,
  Save,
  Download,
  Printer,
  Eye,
  Zap,
  CheckCircle2,
  Settings2,
  Wrench,
  TestTube,
  FileCheck,
  Clipboard,
  ChevronLeft,
  ChevronRight,
  Lock,
  Info,
  Loader2,
  AlertCircle,
  Search,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Link } from "react-router-dom";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Alert, AlertDescription } from "@/components/ui/alert";
import api, { type DatasheetResponse, type FlatDatasheetResponse } from "@/services/api";

// Valve types configuration
const valveTypes = [
  { value: "ball", label: "Ball Valve", prefix: "BS" },
  { value: "gate", label: "Gate Valve", prefix: "GS" },
  { value: "globe", label: "Globe Valve", prefix: "GLS" },
  { value: "check", label: "Check Valve", prefix: "CS" },
  { value: "dbb", label: "Double Block & Bleed (DBB)", prefix: "DSR" },
  { value: "needle", label: "Needle Valve", prefix: "NEE" },
  { value: "butterfly", label: "Butterfly Valve", prefix: "BFD" },
  { value: "plug", label: "Plug Valve", prefix: "PS" },
];

const pipingClasses = [
  { value: "A1", label: "A1 - Carbon Steel" },
  { value: "A2", label: "A2 - Low Alloy Steel" },
  { value: "B1", label: "B1 - Stainless Steel 316" },
  { value: "B2", label: "B2 - Stainless Steel 304" },
  { value: "C1", label: "C1 - Duplex Steel" },
];

const pressureClasses = [
  { value: "ASME B16.34 Class 150", label: "ASME B16.34 Class 150" },
  { value: "ASME B16.34 Class 300", label: "ASME B16.34 Class 300" },
  { value: "ASME B16.34 Class 600", label: "ASME B16.34 Class 600" },
  { value: "ASME B16.34 Class 900", label: "ASME B16.34 Class 900" },
  { value: "ASME B16.34 Class 1500", label: "ASME B16.34 Class 1500" },
  { value: "ASME B16.34 Class 2500", label: "ASME B16.34 Class 2500" },
  { value: "150", label: "Class 150" },
  { value: "300", label: "Class 300" },
  { value: "600", label: "Class 600" },
  { value: "900", label: "Class 900" },
  { value: "1500", label: "Class 1500" },
  { value: "2500", label: "Class 2500" },
];

const valveStandards = [
  { value: "API 6D", label: "API 6D" },
  { value: "API 6D / ISO 17292", label: "API 6D / ISO 17292" },
  { value: "ISO 17292", label: "ISO 17292" },
  { value: "ASME B16.34", label: "ASME B16.34" },
  { value: "BS 5351", label: "BS 5351" },
  { value: "API 600", label: "API 600" },
  { value: "API 600, 602 or API 603", label: "API 600, 602 or API 603" },
  { value: "API 594", label: "API 594" },
  { value: "API 594, API 6D", label: "API 594, API 6D" },
  { value: "API 602", label: "API 602" },
  { value: "API 609", label: "API 609" },
  { value: "API 599", label: "API 599" },
];

const endConnections = [
  { value: "Flanged ASME B16.5 RF", label: "Flanged ASME B16.5 RF" },
  { value: "Flanged ASME B16.5 RTJ", label: "Flanged ASME B16.5 RTJ" },
  { value: "Butt Weld", label: "Butt Weld" },
  { value: "Socket Weld", label: "Socket Weld" },
  { value: "Threaded NPT", label: "Threaded NPT" },
];

const operationModes = [
  { value: "Lever Operated", label: "Lever Operated" },
  { value: "Gear Operated", label: "Gear Operated" },
  { value: "Pneumatic Actuated", label: "Pneumatic Actuated" },
  { value: "Electric Actuated", label: "Electric Actuated" },
  { value: "Hydraulic Actuated", label: "Hydraulic Actuated" },
];

const steps = [
  { id: 1, title: "Basic Info", icon: Settings2, description: "Valve identification & design parameters" },
  { id: 2, title: "Construction", icon: Wrench, description: "Body, ball & operation details" },
  { id: 3, title: "Materials", icon: Clipboard, description: "Component materials specification" },
  { id: 4, title: "Testing", icon: TestTube, description: "Test pressures & requirements" },
  { id: 5, title: "Compliance", icon: FileCheck, description: "Code & certification requirements" },
  { id: 6, title: "Notes", icon: Clipboard, description: "General notes & remarks" },
];

// Default form data
const defaultFormData = {
  vdsNumber: "",
  pipingClass: "",
  sizeRange: "",
  valveType: "",
  boreType: "",
  service: "",
  valveStandard: "",
  pressureClass: "",
  designPressure: "",
  corrosionAllowance: "",
  sourService: "",
  endConnection: "",
  faceToFace: "",
  bodyConstruction: "",
  ballType: "",
  stemType: "",
  seatType: "",
  lockable: true,
  operationMode: "",
  bodyMaterial: "",
  ballMaterial: "",
  seatMaterial: "",
  sealMaterial: "",
  stemMaterial: "",
  glandMaterial: "",
  glandPacking: "",
  leverMaterial: "",
  springMaterial: "",
  gasketMaterial: "",
  boltMaterial: "",
  nutMaterial: "",
  shellTestPressure: "",
  closureTestPressure: "",
  pneumaticTestPressure: "",
  leakageRate: "",
  materialCertification: "",
  fireRating: "",
  inspectionStandard: "",
  sourServiceReq: "none",
  notes: "",
};

export default function DatasheetGeneratorPage() {
  const [formData, setFormData] = useState(defaultFormData);
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [isDataLoaded, setIsDataLoaded] = useState(false);
  const [completionPercentage, setCompletionPercentage] = useState(0);
  const [validationStatus, setValidationStatus] = useState<string | null>(null);
  const { toast } = useToast();

  const updateField = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Map API response to form data
  const mapDatasheetToForm = useCallback((data: FlatDatasheetResponse) => {
    const d = data.data;

    // Helper to safely get string value
    const str = (key: string): string => {
      const val = d[key];
      if (val === null || val === undefined || val === "-") return "";
      return String(val);
    };

    // Helper to get first non-empty value from multiple keys
    const strFirst = (...keys: string[]): string => {
      for (const key of keys) {
        const val = str(key);
        if (val && val !== "-") return val;
      }
      return "";
    };

    // Map valve type from API response to form value
    const mapValveType = (valveTypeStr: string): string => {
      const lower = valveTypeStr.toLowerCase();
      if (lower.includes("ball")) return "ball";
      if (lower.includes("gate")) return "gate";
      if (lower.includes("globe")) return "globe";
      if (lower.includes("check")) return "check";
      if (lower.includes("double") || lower.includes("dbb")) return "dbb";
      if (lower.includes("needle")) return "needle";
      if (lower.includes("butterfly")) return "butterfly";
      if (lower.includes("plug")) return "plug";
      return "ball";
    };

    // Map bore type
    const mapBoreType = (valveTypeStr: string): string => {
      const lower = valveTypeStr.toLowerCase();
      if (lower.includes("full")) return "full";
      if (lower.includes("reduced")) return "reduced";
      return "full";
    };

    // Get ball/disc/wedge construction based on valve type (use first available)
    const ballOrWedgeConstruction = strFirst("ball_construction", "wedge_construction", "disc_construction");

    // Get ball/disc/wedge material based on valve type (use first available)
    const ballOrWedgeMaterial = strFirst("ball_material", "wedge_material", "disc_material", "trim_material");

    setFormData({
      vdsNumber: data.vds_no,
      pipingClass: str("piping_class"),
      sizeRange: str("size_range"),
      valveType: mapValveType(str("valve_type")),
      boreType: mapBoreType(str("valve_type")),
      service: str("service"),
      valveStandard: str("valve_standard"),
      pressureClass: str("pressure_class"),
      designPressure: str("design_pressure"),
      corrosionAllowance: str("corrosion_allowance"),
      sourService: str("sour_service"),
      endConnection: str("end_connections"),
      faceToFace: str("face_to_face"),
      bodyConstruction: str("body_construction"),
      ballType: ballOrWedgeConstruction,
      stemType: str("stem_construction"),
      seatType: str("seat_construction"),
      lockable: true,
      operationMode: str("operation"),
      bodyMaterial: str("body_material"),
      ballMaterial: ballOrWedgeMaterial,
      seatMaterial: str("seat_material"),
      sealMaterial: str("seal_material"),
      stemMaterial: str("stem_material"),
      glandMaterial: str("gland_material"),
      glandPacking: str("gland_packing"),
      leverMaterial: str("lever_handwheel"),
      springMaterial: str("spring_material"),
      gasketMaterial: str("gaskets"),
      boltMaterial: str("bolts"),
      nutMaterial: str("nuts"),
      shellTestPressure: str("hydrotest_shell"),
      closureTestPressure: str("hydrotest_closure"),
      pneumaticTestPressure: str("pneumatic_test"),
      leakageRate: str("leakage_rate"),
      materialCertification: str("material_certification"),
      fireRating: str("fire_rating"),
      inspectionStandard: str("inspection_testing"),
      sourServiceReq: str("sour_service").toLowerCase().includes("nace") ? "nace-mr0175" : "none",
      notes: "",
    });

    setCompletionPercentage(data.completion_percentage);
    setValidationStatus(data.validation_status);
    setIsDataLoaded(true);
  }, []);

  // Fetch datasheet from API
  const fetchDatasheet = useCallback(async (vdsNo: string) => {
    if (vdsNo.length < 5) {
      setFetchError(null);
      return;
    }

    setIsFetching(true);
    setFetchError(null);

    try {
      // First validate the VDS
      const validation = await api.validateVDS(vdsNo);

      if (!validation.is_valid) {
        setFetchError(validation.error || "Invalid VDS number");
        setIsFetching(false);
        return;
      }

      // Fetch the flat datasheet
      const datasheet = await api.generateFlatDatasheet(vdsNo);
      mapDatasheetToForm(datasheet);

      toast({
        title: "Datasheet Loaded",
        description: `VDS ${vdsNo} data populated successfully`,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to fetch datasheet";
      setFetchError(message);
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsFetching(false);
    }
  }, [mapDatasheetToForm, toast]);

  // Handle VDS number input with debounce
  const [vdsInput, setVdsInput] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => {
      if (vdsInput.length >= 5 && vdsInput !== formData.vdsNumber) {
        fetchDatasheet(vdsInput);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [vdsInput, fetchDatasheet, formData.vdsNumber]);

  const handleVdsInputChange = (value: string) => {
    setVdsInput(value.toUpperCase());
    updateField("vdsNumber", value.toUpperCase());
    if (value.length < 5) {
      setFetchError(null);
      setIsDataLoaded(false);
    }
  };

  // Manual fetch trigger
  const handleFetchDatasheet = () => {
    if (formData.vdsNumber.length >= 5) {
      fetchDatasheet(formData.vdsNumber);
    } else {
      toast({
        title: "Invalid VDS",
        description: "Please enter a valid VDS number (minimum 5 characters)",
        variant: "destructive",
      });
    }
  };

  // Reset form
  const handleReset = () => {
    setFormData(defaultFormData);
    setVdsInput("");
    setIsDataLoaded(false);
    setFetchError(null);
    setCompletionPercentage(0);
    setValidationStatus(null);
    toast({
      title: "Form Reset",
      description: "All fields have been cleared",
    });
  };

  const handleExportPDF = () => {
    toast({
      title: "Generating PDF...",
      description: `Creating PDF for VDS: ${formData.vdsNumber || "Draft"}`,
    });

    const printContent = generatePrintableContent();
    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(printContent);
      printWindow.document.close();
      printWindow.onload = () => {
        printWindow.print();
        printWindow.close();
      };
    }
  };

  const generatePrintableContent = () => {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Valve Datasheet - ${formData.vdsNumber || "Draft"}</title>
        <style>
          body { font-family: 'Arial', sans-serif; margin: 40px; color: #333; }
          h1 { color: #1e3a5f; border-bottom: 2px solid #1e3a5f; padding-bottom: 10px; }
          h2 { color: #2563eb; margin-top: 30px; font-size: 16px; background: #f1f5f9; padding: 8px; }
          .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
          .field { margin-bottom: 12px; }
          .label { font-weight: bold; color: #64748b; font-size: 11px; text-transform: uppercase; }
          .value { font-size: 14px; margin-top: 4px; padding: 6px; background: #f8fafc; border-left: 3px solid #2563eb; }
          .header-info { display: flex; justify-content: space-between; margin-bottom: 20px; }
          .badge { background: #22c55e; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #e2e8f0; padding: 8px; text-align: left; font-size: 12px; }
          th { background: #1e3a5f; color: white; }
        </style>
      </head>
      <body>
        <div class="header-info">
          <div>
            <h1>Valve Datasheet Specification</h1>
            <p>VDS Number: <strong>${formData.vdsNumber || "DRAFT"}</strong></p>
          </div>
          <div>
            <span class="badge">${isDataLoaded ? "Generated" : "Draft"}</span>
          </div>
        </div>

        <h2>1. Basic Information</h2>
        <div class="grid">
          <div class="field"><div class="label">Valve Type</div><div class="value">${valveTypes.find((v) => v.value === formData.valveType)?.label || formData.valveType}</div></div>
          <div class="field"><div class="label">Bore Type</div><div class="value">${formData.boreType === "full" ? "Full Bore" : "Reduced Bore"}</div></div>
          <div class="field"><div class="label">Piping Class</div><div class="value">${formData.pipingClass}</div></div>
          <div class="field"><div class="label">Size Range</div><div class="value">${formData.sizeRange}</div></div>
          <div class="field"><div class="label">Valve Standard</div><div class="value">${formData.valveStandard}</div></div>
          <div class="field"><div class="label">Pressure Class</div><div class="value">${formData.pressureClass}</div></div>
          <div class="field"><div class="label">End Connection</div><div class="value">${formData.endConnection}</div></div>
          <div class="field"><div class="label">Face to Face</div><div class="value">${formData.faceToFace}</div></div>
          <div class="field"><div class="label">Design Pressure</div><div class="value">${formData.designPressure}</div></div>
          <div class="field"><div class="label">Corrosion Allowance</div><div class="value">${formData.corrosionAllowance}</div></div>
          <div class="field"><div class="label">Service</div><div class="value">${formData.service || "-"}</div></div>
        </div>

        <h2>2. Construction Details</h2>
        <div class="grid">
          <div class="field"><div class="label">Body Construction</div><div class="value">${formData.bodyConstruction}</div></div>
          <div class="field"><div class="label">Ball Type</div><div class="value">${formData.ballType}</div></div>
          <div class="field"><div class="label">Stem Type</div><div class="value">${formData.stemType}</div></div>
          <div class="field"><div class="label">Seat Type</div><div class="value">${formData.seatType}</div></div>
          <div class="field"><div class="label">Operation Mode</div><div class="value">${formData.operationMode}</div></div>
        </div>

        <h2>3. Materials Specification</h2>
        <table>
          <tr><th>Component</th><th>Material</th></tr>
          <tr><td>Body</td><td>${formData.bodyMaterial}</td></tr>
          <tr><td>Ball/Disc</td><td>${formData.ballMaterial}</td></tr>
          <tr><td>Stem</td><td>${formData.stemMaterial}</td></tr>
          <tr><td>Seat</td><td>${formData.seatMaterial}</td></tr>
          <tr><td>Seal</td><td>${formData.sealMaterial}</td></tr>
          <tr><td>Gland</td><td>${formData.glandMaterial}</td></tr>
          <tr><td>Gland Packing</td><td>${formData.glandPacking}</td></tr>
          <tr><td>Spring</td><td>${formData.springMaterial}</td></tr>
          <tr><td>Gasket</td><td>${formData.gasketMaterial}</td></tr>
          <tr><td>Bolts</td><td>${formData.boltMaterial}</td></tr>
          <tr><td>Nuts</td><td>${formData.nutMaterial}</td></tr>
          <tr><td>Lever/Handwheel</td><td>${formData.leverMaterial}</td></tr>
        </table>

        <h2>4. Test Pressures</h2>
        <div class="grid">
          <div class="field"><div class="label">Shell Test Pressure</div><div class="value">${formData.shellTestPressure || "Not specified"}</div></div>
          <div class="field"><div class="label">Closure Test Pressure</div><div class="value">${formData.closureTestPressure || "Not specified"}</div></div>
          <div class="field"><div class="label">Pneumatic LP Test</div><div class="value">${formData.pneumaticTestPressure || "Not specified"}</div></div>
          <div class="field"><div class="label">Leakage Rate</div><div class="value">${formData.leakageRate}</div></div>
        </div>

        <h2>5. Compliance</h2>
        <div class="grid">
          <div class="field"><div class="label">Fire Rating</div><div class="value">${formData.fireRating}</div></div>
          <div class="field"><div class="label">Material Certification</div><div class="value">${formData.materialCertification}</div></div>
          <div class="field"><div class="label">Inspection Standard</div><div class="value">${formData.inspectionStandard}</div></div>
          <div class="field"><div class="label">Sour Service</div><div class="value">${formData.sourServiceReq === "none" ? "Not Required" : formData.sourServiceReq.toUpperCase()}</div></div>
        </div>

        ${formData.notes ? `<h2>6. Notes</h2><p>${formData.notes}</p>` : ""}

        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #64748b;">
          Generated by ValveFlow Automata • ${new Date().toLocaleDateString()}
        </div>
      </body>
      </html>
    `;
  };

  const handleExportExcel = () => {
    toast({
      title: "Generating Excel...",
      description: `Creating Excel for VDS: ${formData.vdsNumber || "Draft"}`,
    });

    const csvContent = generateCSVContent();
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `valve_datasheet_${formData.vdsNumber || "draft"}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setTimeout(() => {
      toast({
        title: "Excel Ready",
        description: "Your datasheet has been downloaded",
      });
    }, 500);
  };

  const generateCSVContent = () => {
    // Helper to escape CSV values
    const escapeCSV = (val: string) => {
      if (!val) return "";
      if (val.includes(",") || val.includes('"') || val.includes("\n")) {
        return `"${val.replace(/"/g, '""')}"`;
      }
      return val;
    };

    const rows = [
      ["VALVE DATASHEET SPECIFICATION"],
      [""],
      ["Field", "Value"],
      ["VDS Number", escapeCSV(formData.vdsNumber || "DRAFT")],
      ["Generated Date", new Date().toLocaleDateString()],
      ["Status", isDataLoaded ? "Generated from API" : "Draft"],
      ["Completion", isDataLoaded ? `${completionPercentage.toFixed(0)}%` : "N/A"],
      [""],
      ["=== BASIC INFORMATION ===", ""],
      ["Valve Type", escapeCSV(valveTypes.find((v) => v.value === formData.valveType)?.label || formData.valveType)],
      ["Bore Type", formData.boreType === "full" ? "Full Bore" : "Reduced Bore"],
      ["Piping Class", escapeCSV(formData.pipingClass)],
      ["Size Range", escapeCSV(formData.sizeRange)],
      ["Service", escapeCSV(formData.service)],
      [""],
      ["=== DESIGN PARAMETERS ===", ""],
      ["Valve Standard", escapeCSV(formData.valveStandard)],
      ["Pressure Class", escapeCSV(formData.pressureClass)],
      ["Design Pressure", escapeCSV(formData.designPressure)],
      ["Corrosion Allowance", escapeCSV(formData.corrosionAllowance)],
      ["End Connection", escapeCSV(formData.endConnection)],
      ["Face to Face", escapeCSV(formData.faceToFace)],
      [""],
      ["=== CONSTRUCTION DETAILS ===", ""],
      ["Body Construction", escapeCSV(formData.bodyConstruction)],
      ["Ball/Disc Type", escapeCSV(formData.ballType)],
      ["Stem Type", escapeCSV(formData.stemType)],
      ["Seat Type", escapeCSV(formData.seatType)],
      ["Operation Mode", escapeCSV(formData.operationMode)],
      ["Lockable", "Yes - Full Open and Fully Closed"],
      [""],
      ["=== MATERIALS SPECIFICATION ===", ""],
      ["Body Material", escapeCSV(formData.bodyMaterial)],
      ["Ball Material", escapeCSV(formData.ballMaterial)],
      ["Stem Material", escapeCSV(formData.stemMaterial)],
      ["Seat Material", escapeCSV(formData.seatMaterial)],
      ["Seal Material", escapeCSV(formData.sealMaterial)],
      ["Gland Material", escapeCSV(formData.glandMaterial)],
      ["Gland Packing", escapeCSV(formData.glandPacking)],
      ["Spring Material", escapeCSV(formData.springMaterial)],
      ["Gasket Material", escapeCSV(formData.gasketMaterial)],
      ["Bolt Material", escapeCSV(formData.boltMaterial)],
      ["Nut Material", escapeCSV(formData.nutMaterial)],
      ["Lever/Handwheel Material", escapeCSV(formData.leverMaterial)],
      [""],
      ["=== TEST PRESSURES ===", ""],
      ["Shell Test Pressure (Hydrotest)", escapeCSV(formData.shellTestPressure)],
      ["Closure Test Pressure (Hydrotest)", escapeCSV(formData.closureTestPressure)],
      ["Pneumatic LP Test Pressure", escapeCSV(formData.pneumaticTestPressure)],
      ["Leakage Rate", escapeCSV(formData.leakageRate)],
      ["Inspection & Testing Standard", escapeCSV(formData.inspectionStandard)],
      [""],
      ["=== COMPLIANCE & CERTIFICATION ===", ""],
      ["Fire Rating", escapeCSV(formData.fireRating)],
      ["Material Certification", escapeCSV(formData.materialCertification)],
      ["Sour Service", formData.sourServiceReq === "none" ? "Not Required" : formData.sourServiceReq.toUpperCase()],
      [""],
      ["=== NOTES ===", ""],
      ["Notes", escapeCSV(formData.notes || "No additional notes")],
      [""],
      ["=== STANDARD NOTES ===", ""],
      ["1", "This data sheet shall be completed and returned with the quotation."],
      ["2", "Data sheet shall be read in conjunction with Piping Material Specification."],
      ["3", "Hydrostatic shell test pressure shall be 1.5 times of Max. design pressure."],
      ["4", escapeCSV("Ball, Stem and Gland material shall be forged. Castings are not acceptable.")],
      ["5", "All stud bolts and nuts shall be XYLAR 2 + XYLAN 1070 coated."],
    ];

    return rows.map((row) => row.join(",")).join("\n");
  };

  const handleSave = () => {
    toast({
      title: "Datasheet Saved",
      description: "Your valve datasheet has been saved as draft",
    });
  };

  const handlePrint = () => {
    const printContent = generatePrintableContent();
    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(printContent);
      printWindow.document.close();
      printWindow.onload = () => {
        printWindow.print();
      };
    }
  };

  const nextStep = () => setCurrentStep((prev) => Math.min(prev + 1, 6));
  const prevStep = () => setCurrentStep((prev) => Math.max(prev - 1, 1));

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Valve Identification */}
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Valve Identification</CardTitle>
                <CardDescription>Enter VDS number to auto-populate fields</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2 space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      VDS Number
                    </Label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <Input
                          value={formData.vdsNumber}
                          onChange={(e) => handleVdsInputChange(e.target.value)}
                          placeholder="Enter VDS (e.g., BSFA1R)"
                          className={`font-mono text-sm pr-10 ${
                            fetchError ? "border-destructive" : isDataLoaded ? "border-green-500" : ""
                          }`}
                        />
                        {isFetching && (
                          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-muted-foreground" />
                        )}
                        {isDataLoaded && !isFetching && (
                          <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-green-500" />
                        )}
                        {fetchError && !isFetching && (
                          <AlertCircle className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-destructive" />
                        )}
                      </div>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={handleFetchDatasheet}
                            disabled={isFetching || formData.vdsNumber.length < 5}
                          >
                            {isFetching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Fetch Datasheet</TooltipContent>
                      </Tooltip>
                    </div>
                    {fetchError && (
                      <p className="text-xs text-destructive mt-1">{fetchError}</p>
                    )}
                    {isDataLoaded && (
                      <p className="text-xs text-green-600 mt-1">
                        Data loaded • {completionPercentage.toFixed(0)}% complete
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Piping Class
                    </Label>
                    <Select value={formData.pipingClass} onValueChange={(v) => updateField("pipingClass", v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select class" />
                      </SelectTrigger>
                      <SelectContent>
                        {/* Show current value from API if not in predefined list */}
                        {formData.pipingClass && !pipingClasses.some(pc => pc.value === formData.pipingClass) && (
                          <SelectItem key={formData.pipingClass} value={formData.pipingClass}>
                            {formData.pipingClass} (from VDS)
                          </SelectItem>
                        )}
                        {pipingClasses.map((pc) => (
                          <SelectItem key={pc.value} value={pc.value}>
                            {pc.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Valve Type
                    </Label>
                    <Select value={formData.valveType} onValueChange={(v) => updateField("valveType", v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        {valveTypes.map((vt) => (
                          <SelectItem key={vt.value} value={vt.value}>
                            {vt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Bore Type
                    </Label>
                    <Select value={formData.boreType} onValueChange={(v) => updateField("boreType", v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select bore" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="full">Full Bore</SelectItem>
                        <SelectItem value="reduced">Reduced Bore</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Size Range
                    </Label>
                    <Input
                      value={formData.sizeRange}
                      onChange={(e) => updateField("sizeRange", e.target.value)}
                      placeholder='e.g., 1/2" - 24"'
                    />
                  </div>
                  <div className="col-span-2 space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Service Description
                    </Label>
                    <Textarea
                      value={formData.service}
                      onChange={(e) => updateField("service", e.target.value)}
                      placeholder="e.g., Cooling Water, Diesel, Steam"
                      className="min-h-[80px] resize-none"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Design Parameters */}
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Design Parameters</CardTitle>
                <CardDescription>Pressure and temperature ratings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Valve Standard
                    </Label>
                    <Select value={formData.valveStandard} onValueChange={(v) => updateField("valveStandard", v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select standard" />
                      </SelectTrigger>
                      <SelectContent>
                        {valveStandards.map((vs) => (
                          <SelectItem key={vs.value} value={vs.value}>
                            {vs.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Pressure Class
                    </Label>
                    <Select value={formData.pressureClass} onValueChange={(v) => updateField("pressureClass", v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select class" />
                      </SelectTrigger>
                      <SelectContent>
                        {pressureClasses.map((pc) => (
                          <SelectItem key={pc.value} value={pc.value}>
                            {pc.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-2 space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Design Pressure (barg @ Temperature)
                    </Label>
                    <Input
                      value={formData.designPressure}
                      onChange={(e) => updateField("designPressure", e.target.value)}
                      placeholder="e.g., 19.6 @ -29°C, 13.8 @ 200°C"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Corrosion Allowance (mm)
                    </Label>
                    <Input
                      value={formData.corrosionAllowance}
                      onChange={(e) => updateField("corrosionAllowance", e.target.value)}
                      placeholder="e.g., 3"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      End Connection
                    </Label>
                    <Select value={formData.endConnection} onValueChange={(v) => updateField("endConnection", v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select connection" />
                      </SelectTrigger>
                      <SelectContent>
                        {endConnections.map((ec) => (
                          <SelectItem key={ec.value} value={ec.value}>
                            {ec.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-2 space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Face to Face Dimension
                    </Label>
                    <Input
                      value={formData.faceToFace}
                      onChange={(e) => updateField("faceToFace", e.target.value)}
                      placeholder="e.g., ASME B16.10 Long pattern"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 2:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Body & Ball Construction</CardTitle>
                <CardDescription>Valve body and internal components</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Body Construction
                  </Label>
                  <Input
                    value={formData.bodyConstruction}
                    onChange={(e) => updateField("bodyConstruction", e.target.value)}
                    placeholder="e.g., Two piece split body"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Ball Type</Label>
                  <Input
                    value={formData.ballType}
                    onChange={(e) => updateField("ballType", e.target.value)}
                    placeholder="e.g., Floating Ball"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Stem Type</Label>
                  <Input
                    value={formData.stemType}
                    onChange={(e) => updateField("stemType", e.target.value)}
                    placeholder="e.g., Anti-static, Anti blowout proof"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Seat Type</Label>
                  <Input
                    value={formData.seatType}
                    onChange={(e) => updateField("seatType", e.target.value)}
                    placeholder="e.g., Soft Seated, Self-relieving"
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Operation & Locks</CardTitle>
                <CardDescription>Valve operation method</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Operation Mode
                  </Label>
                  {/* If operation mode from API is a detailed description, show as text; otherwise use Select */}
                  {formData.operationMode && !operationModes.some(om => om.value === formData.operationMode) ? (
                    <div className="p-3 bg-muted/30 border rounded-md text-sm">
                      {formData.operationMode}
                    </div>
                  ) : (
                    <Select value={formData.operationMode} onValueChange={(v) => updateField("operationMode", v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select operation mode" />
                      </SelectTrigger>
                      <SelectContent>
                        {operationModes.map((om) => (
                          <SelectItem key={om.value} value={om.value}>
                            {om.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
                <div className="p-4 bg-muted/50 rounded-lg border border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Lock className="w-4 h-4 text-validated" />
                      <div>
                        <p className="text-sm font-medium">Lockable Position</p>
                        <p className="text-xs text-muted-foreground">Full Open, Fully Closed</p>
                      </div>
                    </div>
                    <Badge className="bg-validated-bg text-validated border-0">Enabled</Badge>
                  </div>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg border border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Info className="w-4 h-4 text-primary" />
                      <div>
                        <p className="text-sm font-medium">Position Indicator</p>
                        <p className="text-xs text-muted-foreground">Fully enclosed, dust proof</p>
                      </div>
                    </div>
                    <Badge className="bg-primary/10 text-primary border-0">Included</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 3:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Primary Materials</CardTitle>
                <CardDescription>Body, ball & stem</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Body Material
                  </Label>
                  <Input value={formData.bodyMaterial} onChange={(e) => updateField("bodyMaterial", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Ball Material
                  </Label>
                  <Input value={formData.ballMaterial} onChange={(e) => updateField("ballMaterial", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Stem Material
                  </Label>
                  <Input value={formData.stemMaterial} onChange={(e) => updateField("stemMaterial", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Gland Material
                  </Label>
                  <Input
                    value={formData.glandMaterial}
                    onChange={(e) => updateField("glandMaterial", e.target.value)}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Sealing Materials</CardTitle>
                <CardDescription>Seats, seals & packing</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Seat Material
                  </Label>
                  <Input value={formData.seatMaterial} onChange={(e) => updateField("seatMaterial", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Seal Material
                  </Label>
                  <Input value={formData.sealMaterial} onChange={(e) => updateField("sealMaterial", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Gland Packing
                  </Label>
                  <Input value={formData.glandPacking} onChange={(e) => updateField("glandPacking", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Spring Material
                  </Label>
                  <Input
                    value={formData.springMaterial}
                    onChange={(e) => updateField("springMaterial", e.target.value)}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Hardware Materials</CardTitle>
                <CardDescription>Bolts, nuts & gaskets</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Gasket Material
                  </Label>
                  <Input
                    value={formData.gasketMaterial}
                    onChange={(e) => updateField("gasketMaterial", e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Bolt Material
                  </Label>
                  <Input value={formData.boltMaterial} onChange={(e) => updateField("boltMaterial", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Nut Material
                  </Label>
                  <Input value={formData.nutMaterial} onChange={(e) => updateField("nutMaterial", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Lever Material
                  </Label>
                  <Input
                    value={formData.leverMaterial}
                    onChange={(e) => updateField("leverMaterial", e.target.value)}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 4:
        return (
          <Card className="border-border">
            <CardHeader className="pb-4">
              <CardTitle className="text-base">Test Pressures</CardTitle>
              <CardDescription>Hydrostatic and pneumatic test requirements</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-5 rounded-xl border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <TestTube className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold">Shell Test</p>
                      <p className="text-xs text-muted-foreground">Hydrostatic</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Pressure
                    </Label>
                    <Input
                      value={formData.shellTestPressure}
                      onChange={(e) => updateField("shellTestPressure", e.target.value)}
                      placeholder="e.g., 29.4 barg"
                      className="bg-background"
                    />
                  </div>
                </div>

                <div className="p-5 rounded-xl border-2 border-accent/20 bg-gradient-to-br from-accent/5 to-transparent">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center">
                      <TestTube className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <p className="font-semibold">Closure Test</p>
                      <p className="text-xs text-muted-foreground">Hydrostatic</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Pressure
                    </Label>
                    <Input
                      value={formData.closureTestPressure}
                      onChange={(e) => updateField("closureTestPressure", e.target.value)}
                      placeholder="e.g., 21.56 barg"
                      className="bg-background"
                    />
                  </div>
                </div>

                <div className="p-5 rounded-xl border-2 border-validated/20 bg-gradient-to-br from-validated/5 to-transparent">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-full bg-validated/10 flex items-center justify-center">
                      <TestTube className="w-5 h-5 text-validated" />
                    </div>
                    <div>
                      <p className="font-semibold">Pneumatic LP</p>
                      <p className="text-xs text-muted-foreground">Low Pressure</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Pressure
                    </Label>
                    <Input
                      value={formData.pneumaticTestPressure}
                      onChange={(e) => updateField("pneumaticTestPressure", e.target.value)}
                      placeholder="e.g., 5.5 barg"
                      className="bg-background"
                    />
                  </div>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Leakage Rate Requirement
                  </Label>
                  <Input value={formData.leakageRate} onChange={(e) => updateField("leakageRate", e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Inspection & Testing Standard
                  </Label>
                  <Input
                    value={formData.inspectionStandard}
                    onChange={(e) => updateField("inspectionStandard", e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        );

      case 5:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Code & Compliance</CardTitle>
                <CardDescription>Regulatory and certification requirements</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Fire Safe Rating
                  </Label>
                  <Input
                    value={formData.fireRating}
                    onChange={(e) => updateField("fireRating", e.target.value)}
                    placeholder="e.g., API 607"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Material Certification
                  </Label>
                  <Input
                    value={formData.materialCertification}
                    onChange={(e) => updateField("materialCertification", e.target.value)}
                    placeholder="e.g., EN 10204 3.2"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Sour Service Requirements
                  </Label>
                  <Select value={formData.sourServiceReq} onValueChange={(v) => updateField("sourServiceReq", v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Not Required</SelectItem>
                      <SelectItem value="nace-mr0175">NACE MR0175</SelectItem>
                      <SelectItem value="nace-mr0103">NACE MR0103</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Marking Requirements</CardTitle>
                <CardDescription>Tag and manufacturer marking</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-muted/50 rounded-lg border border-border">
                  <p className="text-sm font-medium mb-1">Purchaser's Specification</p>
                  <p className="text-xs text-muted-foreground">
                    Hard marked with Valve Type on stainless steel label, attached using tamper resistant stainless
                    steel fastener
                  </p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg border border-border">
                  <p className="text-sm font-medium mb-1">Manufacturer Marking</p>
                  <p className="text-xs text-muted-foreground">As per MSS-SP-25</p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg border border-border">
                  <p className="text-sm font-medium mb-1">Finish Specification</p>
                  <p className="text-xs text-muted-foreground">
                    General Specification for Paint and Protective Coating
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 6:
        return (
          <Card className="border-border">
            <CardHeader className="pb-4">
              <CardTitle className="text-base">General Notes & Remarks</CardTitle>
              <CardDescription>Project-specific notes and deviations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                value={formData.notes}
                onChange={(e) => updateField("notes", e.target.value)}
                placeholder="Enter project-specific notes, assumptions, and deviations..."
                className="min-h-[200px] resize-none"
              />

              <div className="p-4 bg-muted/50 rounded-lg border border-border">
                <p className="text-sm font-medium mb-3">Standard Notes</p>
                <div className="space-y-2 text-xs text-muted-foreground">
                  <p>1. This data sheet shall be completed and returned with the quotation.</p>
                  <p>2. Data sheet shall be read in conjunction with Piping Material Specification.</p>
                  <p>3. Hydrostatic shell test pressure shall be 1.5 times of Max. design pressure.</p>
                  <p>4. Ball, Stem and Gland material shall be forged. Castings are not acceptable.</p>
                  <p>5. All stud bolts and nuts shall be XYLAR 2 + XYLAN 1070 coated.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-background">
      <AppHeader
        title="Valve Datasheet Generator"
        breadcrumbs={[{ label: "FPSO Prosperity", href: "/" }, { label: "Valve Datasheet Generator" }]}
      />

      <div className="flex-1 overflow-auto">
        <div className="p-6 space-y-6 animate-fade-in">
          {/* Top Header with Status and Actions */}
          <div className="flex items-center justify-between bg-card border border-border rounded-lg p-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <FileSpreadsheet className="w-6 h-6 text-primary" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-semibold">{formData.vdsNumber || "New Valve Datasheet"}</h2>
                  {isDataLoaded && (
                    <Badge className="bg-validated-bg text-validated border-0 text-xs">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      Loaded from API
                    </Badge>
                  )}
                  {isFetching && (
                    <Badge variant="outline" className="text-xs">
                      <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                      Loading...
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  {formData.valveType ? (valveTypes.find((v) => v.value === formData.valveType)?.label || formData.valveType) : "Select valve type"} •{" "}
                  {formData.pipingClass || "Select piping class"}
                  {isDataLoaded && ` • ${completionPercentage.toFixed(0)}% complete`}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="gap-2" onClick={handleReset}>
                Reset
              </Button>
              <Button variant="outline" size="sm" className="gap-2" onClick={handleSave}>
                <Save className="w-4 h-4" />
                Save
              </Button>
              <Button variant="outline" size="sm" className="gap-2" onClick={handlePrint}>
                <Printer className="w-4 h-4" />
                Print
              </Button>
              <Button variant="outline" size="sm" className="gap-2" onClick={handleExportExcel}>
                <FileSpreadsheet className="w-4 h-4" />
                Excel
              </Button>
              <Button variant="outline" size="sm" className="gap-2" onClick={handleExportPDF}>
                <Download className="w-4 h-4" />
                PDF
              </Button>
              <Link to="/preview">
                <Button variant="outline" size="sm" className="gap-2">
                  <Eye className="w-4 h-4" />
                  Preview
                </Button>
              </Link>
            </div>
          </div>

          {/* API Connection Alert */}
          {!isDataLoaded && !isFetching && (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Enter a VDS number (e.g., <code className="bg-muted px-1 rounded">BSFA1R</code>) to auto-populate all fields from the backend.
                The system will fetch data automatically after you type 5+ characters.
              </AlertDescription>
            </Alert>
          )}

          {/* Progress Stepper */}
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center flex-1">
                  <button
                    onClick={() => setCurrentStep(step.id)}
                    className={`flex items-center gap-3 p-2 rounded-lg transition-all ${
                      currentStep === step.id ? "bg-primary/10" : "hover:bg-muted"
                    }`}
                  >
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all ${
                        currentStep === step.id
                          ? "bg-primary text-primary-foreground"
                          : currentStep > step.id
                            ? "bg-validated text-validated-foreground"
                            : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {currentStep > step.id ? <CheckCircle2 className="w-5 h-5" /> : step.id}
                    </div>
                    <div className="hidden lg:block text-left">
                      <p
                        className={`text-sm font-medium ${currentStep === step.id ? "text-primary" : "text-foreground"}`}
                      >
                        {step.title}
                      </p>
                      <p className="text-xs text-muted-foreground">{step.description}</p>
                    </div>
                  </button>
                  {index < steps.length - 1 && (
                    <div className={`flex-1 h-0.5 mx-2 ${currentStep > step.id ? "bg-validated" : "bg-border"}`} />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Step Content */}
          <div className="min-h-[400px]">{renderStepContent()}</div>

          {/* Navigation Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-border">
            <Button variant="outline" onClick={prevStep} disabled={currentStep === 1} className="gap-2">
              <ChevronLeft className="w-4 h-4" />
              Previous
            </Button>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              Step {currentStep} of {steps.length}
            </div>
            <Button onClick={nextStep} disabled={currentStep === 6} className="gap-2">
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
