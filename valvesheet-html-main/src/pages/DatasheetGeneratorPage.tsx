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
import api, { type DatasheetResponse, type FlatDatasheetResponse, type VDSListResponse, type ValveTypeTemplatesResponse } from "@/services/api";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Command,
  CommandInput,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { cn } from "@/lib/utils";
import html2pdf from 'html2pdf.js';

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

// Mapping from backend field keys to form data keys
const fieldKeyToFormKey: Record<string, string> = {
  // Construction
  body_construction: "bodyConstruction",
  ball_construction: "ballType",
  stem_construction: "stemType",
  seat_construction: "seatType",
  disc_construction: "discConstruction",
  wedge_construction: "wedgeConstruction",
  shaft_construction: "shaftConstruction",
  back_seat_construction: "backSeatConstruction",
  packing_construction: "packingConstruction",
  bonnet_construction: "bonnetConstruction",
  locks: "locks",
  // Material
  body_material: "bodyMaterial",
  ball_material: "ballMaterial",
  stem_material: "stemMaterial",
  seat_material: "seatMaterial",
  seal_material: "sealMaterial",
  gland_material: "glandMaterial",
  gland_packing: "glandPacking",
  lever_handwheel: "leverMaterial",
  spring_material: "springMaterial",
  gaskets: "gasketMaterial",
  bolts: "boltMaterial",
  nuts: "nutMaterial",
  disc_material: "discMaterial",
  wedge_material: "wedgeMaterial",
  trim_material: "trimMaterial",
  shaft_material: "shaftMaterial",
  needle_material: "needleMaterial",
  hinge_pin_material: "hingePinMaterial",
};

// Resolve template key from valve type form value
const resolveTemplateKey = (valveTypeValue: string): string => {
  const typeMap: Record<string, string> = {
    ball: "BALL",
    gate: "GATE",
    globe: "GLOBE",
    check: "CHECK",
    butterfly: "BUTTERFLY",
    dbb: "DDB",
    needle: "NEEDLE",
    plug: "BALL",
  };
  return typeMap[valveTypeValue] || "BALL";
};

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
  // Construction fields (all valve types)
  bodyConstruction: "",
  ballType: "",
  stemType: "",
  seatType: "",
  discConstruction: "",
  wedgeConstruction: "",
  shaftConstruction: "",
  backSeatConstruction: "",
  packingConstruction: "",
  bonnetConstruction: "",
  locks: "",
  lockable: true,
  operationMode: "",
  // Material fields (all valve types)
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
  discMaterial: "",
  wedgeMaterial: "",
  trimMaterial: "",
  shaftMaterial: "",
  needleMaterial: "",
  hingePinMaterial: "",
  // Testing
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
  const [openVdsSelect, setOpenVdsSelect] = useState(false);
  const [allVdsNumbers, setAllVdsNumbers] = useState<string[]>([]);
  const [valveTypeTemplates, setValveTypeTemplates] = useState<ValveTypeTemplatesResponse | null>(null);
  const [activeTemplateKey, setActiveTemplateKey] = useState<string>("BALL");
  const { toast } = useToast();

  // Fetch all VDS numbers and valve type templates on mount
  useEffect(() => {
    const fetchAllVds = async () => {
      try {
        const response: VDSListResponse = await api.getVDSNumbers({ limit: 1000 });
        setAllVdsNumbers(response.vds_numbers);
      } catch (error) {
        console.error("Failed to fetch all VDS numbers:", error);
        toast({
          title: "Error",
          description: "Failed to load VDS suggestions.",
          variant: "destructive",
        });
      }
    };
    const fetchTemplates = async () => {
      try {
        const response = await api.getValveTypeTemplates();
        setValveTypeTemplates(response);
        setActiveTemplateKey(response.default_template);
      } catch (error) {
        console.error("Failed to fetch valve type templates:", error);
      }
    };
    fetchAllVds();
    fetchTemplates();
  }, [toast]);

  // Auto-switch template when valve type changes
  useEffect(() => {
    if (formData.valveType) {
      setActiveTemplateKey(resolveTemplateKey(formData.valveType));
    }
  }, [formData.valveType]);

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

    const resolvedValveType = mapValveType(str("valve_type"));

    setFormData({
      vdsNumber: data.vds_no,
      pipingClass: str("piping_class"),
      sizeRange: str("size_range"),
      valveType: resolvedValveType,
      boreType: mapBoreType(str("valve_type")),
      service: str("service"),
      valveStandard: str("valve_standard"),
      pressureClass: str("pressure_class"),
      designPressure: str("design_pressure"),
      corrosionAllowance: str("corrosion_allowance"),
      sourService: str("sour_service"),
      endConnection: str("end_connections"),
      faceToFace: str("face_to_face"),
      // Construction fields - map each directly
      bodyConstruction: str("body_construction"),
      ballType: str("ball_construction"),
      stemType: str("stem_construction"),
      seatType: str("seat_construction"),
      discConstruction: str("disc_construction"),
      wedgeConstruction: str("wedge_construction"),
      shaftConstruction: str("shaft_construction"),
      backSeatConstruction: str("back_seat_construction"),
      packingConstruction: str("packing_construction"),
      bonnetConstruction: str("bonnet_construction"),
      locks: str("locks"),
      lockable: true,
      operationMode: str("operation"),
      // Material fields - map each directly
      bodyMaterial: str("body_material"),
      ballMaterial: str("ball_material"),
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
      discMaterial: str("disc_material"),
      wedgeMaterial: str("wedge_material"),
      trimMaterial: str("trim_material"),
      shaftMaterial: str("shaft_material"),
      needleMaterial: str("needle_material"),
      hingePinMaterial: str("hinge_pin_material"),
      // Testing
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

    // Auto-switch template based on decoded valve type
    setActiveTemplateKey(resolveTemplateKey(resolvedValveType));

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

    const content = generatePrintableContent();
    const element = document.createElement('div');
    element.innerHTML = content;

    html2pdf().from(element).set({
      margin: 10,
      filename: `valve_datasheet_${formData.vdsNumber || "draft"}.pdf`,
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    }).save();

    toast({
      title: "PDF Ready",
      description: "Your datasheet has been downloaded as PDF",
    });
  };

  const generatePrintableContent = () => {
    const template = valveTypeTemplates?.templates[activeTemplateKey];
    const fd = formData as Record<string, unknown>;

    // Dynamic construction rows
    const constructionRows = (template?.construction_fields || [])
      .filter(f => f.key !== "locks")
      .map(f => {
        const formKey = fieldKeyToFormKey[f.key] || f.key;
        const value = (fd[formKey] as string) || "";
        return `<div class="field"><div class="label">${f.label}</div><div class="value">${value || "-"}</div></div>`;
      }).join("\n          ");

    // Dynamic material rows
    const materialRows = (template?.material_fields || [])
      .map(f => {
        const formKey = fieldKeyToFormKey[f.key] || f.key;
        const value = (fd[formKey] as string) || "";
        return `<tr><td>${f.label}</td><td>${value || "-"}</td></tr>`;
      }).join("\n          ");

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
          ${constructionRows}
          <div class="field"><div class="label">Operation Mode</div><div class="value">${formData.operationMode}</div></div>
        </div>

        <h2>3. Materials Specification</h2>
        <table>
          <tr><th>Component</th><th>Material</th></tr>
          ${materialRows}
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
    const template = valveTypeTemplates?.templates[activeTemplateKey];
    const fd = formData as Record<string, unknown>;

    // Helper to escape CSV values
    const escapeCSV = (val: string) => {
      if (!val) return "";
      if (val.includes(",") || val.includes('"') || val.includes("\n")) {
        return `"${val.replace(/"/g, '""')}"`;
      }
      return val;
    };

    // Dynamic construction rows
    const constructionRows: string[][] = (template?.construction_fields || [])
      .filter(f => f.key !== "locks")
      .map(f => {
        const formKey = fieldKeyToFormKey[f.key] || f.key;
        return [f.label, escapeCSV((fd[formKey] as string) || "")];
      });
    constructionRows.push(["Operation Mode", escapeCSV(formData.operationMode)]);
    constructionRows.push(["Lockable", formData.locks || "Yes - Full Open and Fully Closed"]);

    // Dynamic material rows
    const materialRows: string[][] = (template?.material_fields || [])
      .map(f => {
        const formKey = fieldKeyToFormKey[f.key] || f.key;
        return [f.label, escapeCSV((fd[formKey] as string) || "")];
      });

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
      ...constructionRows,
      [""],
      ["=== MATERIALS SPECIFICATION ===", ""],
      ...materialRows,
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
                      <Popover open={openVdsSelect} onOpenChange={setOpenVdsSelect}>
                        <PopoverTrigger asChild>
                          <Button
                            variant="outline"
                            role="combobox"
                            aria-expanded={openVdsSelect}
                            className={cn(
                              "w-full justify-between font-mono text-sm",
                              formData.vdsNumber ? "" : "text-muted-foreground",
                              fetchError ? "border-destructive" : isDataLoaded ? "border-green-500" : ""
                            )}
                          >
                            {formData.vdsNumber
                              ? formData.vdsNumber
                              : "Select VDS Number..."}
                            {isFetching && (
                              <Loader2 className="ml-2 h-4 w-4 shrink-0 opacity-50 animate-spin" />
                            )}
                            {isDataLoaded && !isFetching && (
                              <CheckCircle2 className="ml-2 h-4 w-4 shrink-0 text-green-500" />
                            )}
                            {fetchError && !isFetching && (
                              <AlertCircle className="ml-2 h-4 w-4 shrink-0 text-destructive" />
                            )}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0">
                          <Command>
                            <CommandInput
                              placeholder="Search VDS number..."
                              value={vdsInput}
                              onValueChange={(val) => setVdsInput(val.toUpperCase())}
                            />
                            <CommandEmpty>No VDS number found.</CommandEmpty>
                            <CommandGroup>
                              <CommandList>
                                {allVdsNumbers
                                  .filter((vds) => vds.toUpperCase().includes(vdsInput))
                                  .map((vds) => (
                                    <CommandItem
                                      key={vds}
                                      value={vds}
                                      onSelect={(currentValue) => {
                                        const selectedVds = currentValue.toUpperCase();
                                        setVdsInput(selectedVds);
                                        updateField("vdsNumber", selectedVds);
                                        fetchDatasheet(selectedVds);
                                        setOpenVdsSelect(false);
                                      }}
                                    >
                                      {vds}
                                    </CommandItem>
                                  ))}
                              </CommandList>
                            </CommandGroup>
                          </Command>
                        </PopoverContent>
                      </Popover>
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

      case 2: {
        const template = valveTypeTemplates?.templates[activeTemplateKey];
        const constructionFields = template?.construction_fields || [
          { key: "body_construction", label: "Body" },
          { key: "ball_construction", label: "Ball" },
          { key: "stem_construction", label: "Stem" },
          { key: "seat_construction", label: "Seat" },
          { key: "locks", label: "Locks" },
        ];
        const hasLocks = constructionFields.some(f => f.key === "locks");
        const inputFields = constructionFields.filter(f => f.key !== "locks");

        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">
                  {template?.display_name || "Ball Valve"} - Construction
                </CardTitle>
                <CardDescription>Valve body and internal components</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {inputFields.map((field) => {
                  const formKey = fieldKeyToFormKey[field.key] || field.key;
                  return (
                    <div key={field.key} className="space-y-2">
                      <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        {field.label}
                      </Label>
                      <Input
                        value={(formData as Record<string, unknown>)[formKey] as string || ""}
                        onChange={(e) => updateField(formKey, e.target.value)}
                        placeholder={`Enter ${field.label.toLowerCase()}`}
                      />
                    </div>
                  );
                })}
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
                {hasLocks && (
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Lock className="w-4 h-4 text-validated" />
                        <div>
                          <p className="text-sm font-medium">Lockable Position</p>
                          <p className="text-xs text-muted-foreground">
                            {formData.locks || "Full Open, Fully Closed"}
                          </p>
                        </div>
                      </div>
                      <Badge className="bg-validated-bg text-validated border-0">Enabled</Badge>
                    </div>
                  </div>
                )}
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
      }

      case 3: {
        const template = valveTypeTemplates?.templates[activeTemplateKey];
        const materialFields = template?.material_fields || [
          { key: "body_material", label: "Body" },
          { key: "ball_material", label: "Ball" },
          { key: "stem_material", label: "Stem" },
          { key: "seat_material", label: "Seat" },
          { key: "gland_material", label: "Gland" },
          { key: "gland_packing", label: "Gland Packing" },
          { key: "lever_handwheel", label: "Lever / Handwheel" },
          { key: "spring_material", label: "Spring" },
          { key: "gaskets", label: "Gaskets" },
          { key: "bolts", label: "Bolts" },
          { key: "nuts", label: "Nuts" },
        ];

        // Split into 3 groups for the 3-column layout
        const groupSize = Math.ceil(materialFields.length / 3);
        const groups = [
          { title: "Primary Materials", desc: "Structural components", fields: materialFields.slice(0, groupSize) },
          { title: "Sealing Materials", desc: "Seats, seals & packing", fields: materialFields.slice(groupSize, groupSize * 2) },
          { title: "Hardware Materials", desc: "Fasteners & accessories", fields: materialFields.slice(groupSize * 2) },
        ].filter(g => g.fields.length > 0);

        return (
          <div className={`grid grid-cols-1 ${groups.length === 2 ? "lg:grid-cols-2" : "lg:grid-cols-3"} gap-6`}>
            {groups.map((group) => (
              <Card key={group.title} className="border-border">
                <CardHeader className="pb-4">
                  <CardTitle className="text-base">{group.title}</CardTitle>
                  <CardDescription>{group.desc}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {group.fields.map((field) => {
                    const formKey = fieldKeyToFormKey[field.key] || field.key;
                    return (
                      <div key={field.key} className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          {field.label}
                        </Label>
                        <Input
                          value={(formData as Record<string, unknown>)[formKey] as string || ""}
                          onChange={(e) => updateField(formKey, e.target.value)}
                          placeholder={`Enter ${field.label.toLowerCase()}`}
                        />
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            ))}
          </div>
        );
      }

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
