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
import api, { type DatasheetResponse, type FlatDatasheetResponse, type VDSListResponse, type ValveTypeTemplatesResponse, type MLFlatPredictionResponse } from "@/services/api";
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

// Field display names for dynamic rendering
const fieldDisplayNames: Record<string, string> = {
  // Basic Info
  vds_no: "VDS Number",
  piping_class: "Piping Class",
  size_range: "Size Range",
  valve_type: "Valve Type",
  service: "Service",
  valve_standard: "Valve Standard",
  pressure_class: "Pressure Class",
  design_pressure: "Design Pressure",
  corrosion_allowance: "Corrosion Allowance",
  sour_service: "Sour Service",
  end_connections: "End Connection",
  face_to_face: "Face to Face",
  // Construction (no "Construction" suffix)
  body_construction: "Body",
  ball_construction: "Ball",
  stem_construction: "Stem",
  seat_construction: "Seat",
  disc_construction: "Disc",
  wedge_construction: "Wedge",
  shaft_construction: "Shaft",
  back_seat_construction: "Back Seat",
  packing_construction: "Packing",
  bonnet_construction: "Bonnet",
  construction_bonnet: "Bonnet",
  locks: "Locks",
  operation: "Operation",
  // Materials (no "Material" suffix)
  body_material: "Body",
  ball_material: "Ball",
  stem_material: "Stem",
  seat_material: "Seat",
  seal_material: "Seal",
  gland_material: "Gland",
  gland_packing: "Gland Packing",
  lever_handwheel: "Lever / Handwheel",
  spring_material: "Spring",
  gaskets: "Gaskets",
  bolts: "Bolts",
  nuts: "Nuts",
  disc_material: "Disc",
  wedge_material: "Wedge",
  trim_material: "Trim",
  shaft_material: "Shaft",
  needle_material: "Needle",
  material_needle_material: "Needle",
  back_seat_material: "Back Seat",
  hinge_pin_material: "Hinge Pin",
  material_cover_material: "Cover",
  "material_hinge/_hinge_pin": "Hinge / Hinge Pin",
  // Testing
  hydrotest_shell: "Shell Test Pressure",
  hydrotest_closure: "Closure Test Pressure",
  pneumatic_test: "Pneumatic Test Pressure",
  leakage_rate: "Leakage Rate",
  inspection_testing: "Inspection & Testing",
  // Compliance
  material_certification: "Material Certification",
  fire_rating: "Fire Rating",
  marking_purchaser: "Marking (Purchaser)",
  marking_manufacturer: "Marking (Manufacturer)",
  finish: "Finish",
};

// Field categories for grouping in UI
const fieldCategories: Record<string, string[]> = {
  basic: [
    "vds_no", "piping_class", "size_range", "valve_type", "service",
    "valve_standard", "pressure_class", "design_pressure", "corrosion_allowance",
    "sour_service", "end_connections", "face_to_face"
  ],
  construction: [
    "body_construction", "ball_construction", "stem_construction", "seat_construction",
    "disc_construction", "wedge_construction", "shaft_construction", "back_seat_construction",
    "packing_construction", "bonnet_construction", "construction_bonnet", "locks", "operation"
  ],
  materials: [
    "body_material", "ball_material", "stem_material", "seat_material", "seal_material",
    "gland_material", "gland_packing", "lever_handwheel", "spring_material", "gaskets",
    "bolts", "nuts", "disc_material", "wedge_material", "trim_material", "shaft_material",
    "needle_material", "material_needle_material", "back_seat_material", "hinge_pin_material",
    "material_cover_material", "material_hinge/_hinge_pin"
  ],
  testing: [
    "hydrotest_shell", "hydrotest_closure", "pneumatic_test", "leakage_rate", "inspection_testing"
  ],
  compliance: [
    "material_certification", "fire_rating", "marking_purchaser", "marking_manufacturer", "finish"
  ],
};

// Legacy mapping (kept for PDF/CSV export compatibility)
const fieldKeyToFormKey: Record<string, string> = {
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
  const [activeFields, setActiveFields] = useState<Set<string>>(new Set()); // Fields returned from ML API
  const [mlData, setMlData] = useState<Record<string, string>>({}); // Raw ML data for dynamic rendering
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

  // Map API response to form data (legacy rule-based endpoint)
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

  // Map ML prediction response to form data (only populates returned fields)
  const mapMLPredictionToForm = useCallback((data: MLFlatPredictionResponse) => {
    const d = data.data;

    // Store raw ML data for dynamic rendering
    setMlData(d);

    // Track which fields were returned from ML API
    const returnedFields = new Set(Object.keys(d));
    setActiveFields(returnedFields);

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

    // Build form data, only setting fields that are returned from ML
    const newFormData = {
      ...defaultFormData,
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
      // Construction fields
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
      // Material fields
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
    };

    setFormData(newFormData);

    // Auto-switch template based on decoded valve type
    setActiveTemplateKey(resolveTemplateKey(resolvedValveType));

    // Calculate completion percentage from returned fields
    const totalFields = returnedFields.size;
    const populatedFields = Object.values(d).filter(v => v !== "" && v !== null && v !== undefined && v !== "-").length;
    setCompletionPercentage((populatedFields / totalFields) * 100);
    setValidationStatus("valid");
    setIsDataLoaded(true);
  }, []);

  // Fetch datasheet from ML API (production endpoint)
  const fetchDatasheet = useCallback(async (vdsNo: string) => {
    if (vdsNo.length < 5) {
      setFetchError(null);
      return;
    }

    setIsFetching(true);
    setFetchError(null);

    try {
      // Use ML prediction endpoint (returns only valve-type-specific fields)
      const mlPrediction = await api.getMLPrediction(vdsNo);
      mapMLPredictionToForm(mlPrediction);

      toast({
        title: "Datasheet Loaded",
        description: `VDS ${vdsNo} data populated from ML prediction`,
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
  }, [mapMLPredictionToForm, toast]);

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
    setActiveFields(new Set()); // Reset active fields
    setMlData({}); // Reset ML data
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
    // Get dynamic fields from ML data
    const constructionFieldKeys = fieldCategories.construction.filter(key => activeFields.has(key));
    const materialFieldKeys = fieldCategories.materials.filter(key => activeFields.has(key));
    const testingFieldKeys = fieldCategories.testing.filter(key => activeFields.has(key));
    const complianceFieldKeys = fieldCategories.compliance.filter(key => activeFields.has(key));

    // Dynamic construction rows from ML data
    const constructionRows = constructionFieldKeys
      .map(key => {
        const displayName = fieldDisplayNames[key] || key.replace(/_/g, " ");
        const value = mlData[key] || "-";
        return `<div class="field"><span class="label">${displayName}:</span> <span class="value">${value}</span></div>`;
      }).join("\n          ");

    // Dynamic material rows from ML data
    const materialRows = materialFieldKeys
      .map(key => {
        const displayName = fieldDisplayNames[key] || key.replace(/_/g, " ");
        const value = mlData[key] || "-";
        return `<tr><td>${displayName}</td><td>${value}</td></tr>`;
      }).join("\n          ");

    // Dynamic testing rows
    const testingRows = testingFieldKeys
      .map(key => {
        const displayName = fieldDisplayNames[key] || key.replace(/_/g, " ");
        const value = mlData[key] || "-";
        return `<div class="field"><span class="label">${displayName}:</span> <span class="value">${value}</span></div>`;
      }).join("\n          ");

    // Dynamic compliance rows
    const complianceRows = complianceFieldKeys
      .map(key => {
        const displayName = fieldDisplayNames[key] || key.replace(/_/g, " ");
        const value = mlData[key] || "-";
        return `<div class="field"><span class="label">${displayName}:</span> <span class="value">${value}</span></div>`;
      }).join("\n          ");

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Valve Datasheet - ${formData.vdsNumber || "Draft"}</title>
        <style>
          @page { size: A4; margin: 10mm; }
          body { font-family: 'Arial', sans-serif; margin: 10px; color: #333; font-size: 9px; }
          h1 { color: #1e3a5f; border-bottom: 1px solid #1e3a5f; padding-bottom: 4px; margin: 0 0 8px 0; font-size: 14px; }
          h2 { color: #2563eb; margin: 8px 0 4px 0; font-size: 10px; background: #f1f5f9; padding: 3px 6px; }
          .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2px 12px; }
          .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 2px 12px; }
          .field { margin-bottom: 2px; line-height: 1.3; }
          .label { font-weight: bold; color: #64748b; }
          .value { color: #1e293b; }
          .header-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
          .badge { background: #22c55e; color: white; padding: 2px 8px; border-radius: 3px; font-size: 8px; }
          table { width: 100%; border-collapse: collapse; margin-top: 4px; font-size: 8px; }
          th, td { border: 1px solid #e2e8f0; padding: 3px 5px; text-align: left; }
          th { background: #1e3a5f; color: white; }
          .footer { margin-top: 8px; padding-top: 4px; border-top: 1px solid #e2e8f0; font-size: 8px; color: #64748b; }
        </style>
      </head>
      <body>
        <div class="header-info">
          <h1>Valve Datasheet - ${formData.vdsNumber || "DRAFT"}</h1>
          <span class="badge">${isDataLoaded ? "Generated" : "Draft"}</span>
        </div>

        <h2>Basic Information</h2>
        <div class="grid-3">
          <div class="field"><span class="label">Valve Type:</span> <span class="value">${mlData["valve_type"] || "-"}</span></div>
          <div class="field"><span class="label">Piping Class:</span> <span class="value">${mlData["piping_class"] || "-"}</span></div>
          <div class="field"><span class="label">Size Range:</span> <span class="value">${formData.sizeRange || "-"}</span></div>
          <div class="field"><span class="label">Valve Standard:</span> <span class="value">${mlData["valve_standard"] || "-"}</span></div>
          <div class="field"><span class="label">Pressure Class:</span> <span class="value">${mlData["pressure_class"] || "-"}</span></div>
          <div class="field"><span class="label">Design Pressure:</span> <span class="value">${mlData["design_pressure"] || "-"}</span></div>
          <div class="field"><span class="label">End Connection:</span> <span class="value">${mlData["end_connections"] || "-"}</span></div>
          <div class="field"><span class="label">Face to Face:</span> <span class="value">${mlData["face_to_face"] || "-"}</span></div>
          <div class="field"><span class="label">Corrosion Allowance:</span> <span class="value">${mlData["corrosion_allowance"] || "-"}</span></div>
          <div class="field"><span class="label">Service:</span> <span class="value">${formData.service || "-"}</span></div>
          <div class="field"><span class="label">Sour Service:</span> <span class="value">${mlData["sour_service"] || "-"}</span></div>
        </div>

        ${constructionRows ? `<h2>Construction</h2><div class="grid">${constructionRows}</div>` : ""}

        ${materialRows ? `<h2>Materials</h2><table><tr><th>Component</th><th>Material</th></tr>${materialRows}</table>` : ""}

        ${testingRows ? `<h2>Testing</h2><div class="grid">${testingRows}</div>` : ""}

        ${complianceRows ? `<h2>Compliance</h2><div class="grid">${complianceRows}</div>` : ""}

        <div class="footer">
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
                <CardDescription>Valve identification</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2 space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      VDS Number
                    </Label>
                    <div className="relative">
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <Input
                            value={vdsInput}
                            onChange={(e) => {
                              const val = e.target.value.toUpperCase();
                              setVdsInput(val);
                              handleVdsInputChange(val);
                              setOpenVdsSelect(val.length > 0);
                            }}
                            onFocus={() => setOpenVdsSelect(vdsInput.length > 0)}
                            placeholder="Type VDS number..."
                            className={cn(
                              "font-mono text-sm",
                              fetchError ? "border-destructive" : isDataLoaded ? "border-green-500" : ""
                            )}
                          />
                          {isFetching && (
                            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
                          )}
                          {isDataLoaded && !isFetching && (
                            <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-green-500" />
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
                      {/* Autocomplete dropdown */}
                      {openVdsSelect && vdsInput.length > 0 && (
                        <div className="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-md max-h-[200px] overflow-auto">
                          {allVdsNumbers
                            .filter((vds) => vds.toUpperCase().includes(vdsInput))
                            .slice(0, 5)
                            .map((vds) => (
                              <div
                                key={vds}
                                className="px-3 py-2 text-sm cursor-pointer hover:bg-accent font-mono"
                                onClick={() => {
                                  setVdsInput(vds);
                                  updateField("vdsNumber", vds);
                                  fetchDatasheet(vds);
                                  setOpenVdsSelect(false);
                                }}
                              >
                                {vds}
                              </div>
                            ))}
                          {allVdsNumbers.filter((vds) => vds.toUpperCase().includes(vdsInput)).length === 0 && (
                            <div className="px-3 py-2 text-sm text-muted-foreground">No VDS found</div>
                          )}
                        </div>
                      )}
                    </div>
                    {fetchError && (
                      <p className="text-xs text-destructive mt-1">{fetchError}</p>
                    )}
                    {isDataLoaded && (
                      <p className="text-xs text-green-600 mt-1">
                        {activeFields.size} fields loaded
                      </p>
                    )}
                  </div>
                  {/* Dynamic fields from ML - only show if data loaded */}
                  {isDataLoaded && activeFields.has("valve_type") && (
                    <div className="col-span-2 space-y-2">
                      <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Valve Type
                      </Label>
                      <div className="p-3 bg-muted/30 border rounded-md text-sm font-medium">
                        {mlData["valve_type"] || "-"}
                      </div>
                    </div>
                  )}
                  {isDataLoaded && activeFields.has("piping_class") && (
                    <div className="space-y-2">
                      <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Piping Class
                      </Label>
                      <div className="p-3 bg-muted/30 border rounded-md text-sm">
                        {mlData["piping_class"] || "-"}
                      </div>
                    </div>
                  )}
                  {isDataLoaded && activeFields.has("size_range") && (
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
                  )}
                  {isDataLoaded && activeFields.has("service") && (
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
                  )}
                  {/* Show empty non-editable fields when no data loaded */}
                  {!isDataLoaded && (
                    <>
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Valve Type
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm text-muted-foreground">-</div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Piping Class
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm text-muted-foreground">-</div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Size Range
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm text-muted-foreground">-</div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Service
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm text-muted-foreground">-</div>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Design Parameters */}
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Design Parameters</CardTitle>
                <CardDescription>
                  Pressure and temperature ratings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  {/* Show dynamic fields when data is loaded */}
                  {isDataLoaded ? (
                    <>
                      {activeFields.has("valve_standard") && (
                        <div className="col-span-2 space-y-2">
                          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            Valve Standard
                          </Label>
                          <div className="p-3 bg-muted/30 border rounded-md text-sm">
                            {mlData["valve_standard"] || "-"}
                          </div>
                        </div>
                      )}
                      {activeFields.has("pressure_class") && (
                        <div className="space-y-2">
                          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            Pressure Class
                          </Label>
                          <div className="p-3 bg-muted/30 border rounded-md text-sm">
                            {mlData["pressure_class"] || "-"}
                          </div>
                        </div>
                      )}
                      {activeFields.has("design_pressure") && (
                        <div className="space-y-2">
                          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            Design Pressure
                          </Label>
                          <div className="p-3 bg-muted/30 border rounded-md text-sm">
                            {mlData["design_pressure"] || "-"}
                          </div>
                        </div>
                      )}
                      {activeFields.has("corrosion_allowance") && (
                        <div className="space-y-2">
                          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            Corrosion Allowance
                          </Label>
                          <div className="p-3 bg-muted/30 border rounded-md text-sm">
                            {mlData["corrosion_allowance"] || "-"}
                          </div>
                        </div>
                      )}
                      {activeFields.has("end_connections") && (
                        <div className="space-y-2">
                          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            End Connection
                          </Label>
                          <div className="p-3 bg-muted/30 border rounded-md text-sm">
                            {mlData["end_connections"] || "-"}
                          </div>
                        </div>
                      )}
                      {activeFields.has("face_to_face") && (
                        <div className="space-y-2">
                          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            Face to Face
                          </Label>
                          <div className="p-3 bg-muted/30 border rounded-md text-sm">
                            {mlData["face_to_face"] || "-"}
                          </div>
                        </div>
                      )}
                      {activeFields.has("sour_service") && (
                        <div className="col-span-2 space-y-2">
                          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            Sour Service
                          </Label>
                          <div className="p-3 bg-muted/30 border rounded-md text-sm">
                            {mlData["sour_service"] || "-"}
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <>
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Valve Standard
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm text-muted-foreground">-</div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Pressure Class
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm text-muted-foreground">-</div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Design Pressure
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm text-muted-foreground">-</div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Corrosion Allowance
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm text-muted-foreground">-</div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          End Connection
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm text-muted-foreground">-</div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Face to Face
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm text-muted-foreground">-</div>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 2: {
        // Get construction fields dynamically from ML data (including locks and operation)
        const constructionFieldKeys = fieldCategories.construction.filter(key => activeFields.has(key));

        return (
          <Card className="border-border">
            <CardHeader className="pb-4">
              <CardTitle className="text-base">Construction Details</CardTitle>
              <CardDescription>Valve body and internal components</CardDescription>
            </CardHeader>
            <CardContent>
              {!isDataLoaded ? (
                <div className="text-sm text-muted-foreground">-</div>
              ) : constructionFieldKeys.length === 0 ? (
                <div className="text-sm text-muted-foreground italic">
                  No construction fields returned for this valve type
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {constructionFieldKeys.map((fieldKey) => {
                    const displayName = fieldDisplayNames[fieldKey] || fieldKey.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
                    const value = mlData[fieldKey] || "";
                    return (
                      <div key={fieldKey} className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          {displayName}
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm">
                          {value || "-"}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        );
      }

      case 3: {
        // Get material fields dynamically from ML data
        const materialFieldKeys = fieldCategories.materials.filter(key => activeFields.has(key));

        if (!isDataLoaded) {
          return (
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Materials Specification</CardTitle>
                <CardDescription>Component materials</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">-</div>
              </CardContent>
            </Card>
          );
        }

        if (materialFieldKeys.length === 0) {
          return (
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Materials Specification</CardTitle>
                <CardDescription>No material fields returned for this valve type</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground italic">
                  The ML prediction did not return any material fields for this VDS number.
                </div>
              </CardContent>
            </Card>
          );
        }

        // Split into 3 groups for the 3-column layout
        const groupSize = Math.ceil(materialFieldKeys.length / 3);
        const groups = [
          { title: "Primary Materials", desc: "Structural components", fields: materialFieldKeys.slice(0, groupSize) },
          { title: "Sealing Materials", desc: "Seats, seals & packing", fields: materialFieldKeys.slice(groupSize, groupSize * 2) },
          { title: "Hardware Materials", desc: "Fasteners & accessories", fields: materialFieldKeys.slice(groupSize * 2) },
        ].filter(g => g.fields.length > 0);

        return (
          <div className={`grid grid-cols-1 ${groups.length === 2 ? "lg:grid-cols-2" : "lg:grid-cols-3"} gap-6`}>
            {groups.map((group) => (
              <Card key={group.title} className="border-border">
                <CardHeader className="pb-4">
                  <CardTitle className="text-base">{group.title}</CardTitle>
                  <CardDescription>
                    {group.fields.length} fields
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {group.fields.map((fieldKey) => {
                    const displayName = fieldDisplayNames[fieldKey] || fieldKey.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
                    const value = mlData[fieldKey] || "";
                    return (
                      <div key={fieldKey} className="space-y-2">
                        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          {displayName}
                        </Label>
                        <div className="p-3 bg-muted/30 border rounded-md text-sm whitespace-pre-wrap">
                          {value || "-"}
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            ))}
          </div>
        );
      }

      case 4: {
        // Get testing fields dynamically from ML data
        const testingFieldKeys = fieldCategories.testing.filter(key => activeFields.has(key));

        if (!isDataLoaded) {
          return (
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Test Pressures</CardTitle>
                <CardDescription>Test requirements</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">-</div>
              </CardContent>
            </Card>
          );
        }

        if (testingFieldKeys.length === 0) {
          return (
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Test Pressures</CardTitle>
                <CardDescription>No test fields returned for this valve type</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground italic">
                  The ML prediction did not return any test fields for this VDS number.
                </div>
              </CardContent>
            </Card>
          );
        }

        return (
          <Card className="border-border">
            <CardHeader className="pb-4">
              <CardTitle className="text-base">Test Pressures</CardTitle>
              <CardDescription>{testingFieldKeys.length} fields</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {activeFields.has("hydrotest_shell") && (
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
                    <div className="p-3 bg-background border rounded-md text-sm font-medium">
                      {mlData["hydrotest_shell"] || "-"}
                    </div>
                  </div>
                )}

                {activeFields.has("hydrotest_closure") && (
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
                    <div className="p-3 bg-background border rounded-md text-sm font-medium">
                      {mlData["hydrotest_closure"] || "-"}
                    </div>
                  </div>
                )}

                {activeFields.has("pneumatic_test") && (
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
                    <div className="p-3 bg-background border rounded-md text-sm font-medium">
                      {mlData["pneumatic_test"] || "-"}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 grid grid-cols-2 gap-4">
                {activeFields.has("leakage_rate") && (
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Leakage Rate Requirement
                    </Label>
                    <div className="p-3 bg-muted/30 border rounded-md text-sm">
                      {mlData["leakage_rate"] || "-"}
                    </div>
                  </div>
                )}
                {activeFields.has("inspection_testing") && (
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Inspection & Testing Standard
                    </Label>
                    <div className="p-3 bg-muted/30 border rounded-md text-sm">
                      {mlData["inspection_testing"] || "-"}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        );
      }

      case 5: {
        // Get compliance fields dynamically from ML data
        const complianceFieldKeys = fieldCategories.compliance.filter(key => activeFields.has(key));

        if (!isDataLoaded) {
          return (
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Compliance & Certification</CardTitle>
                <CardDescription>Regulatory and certification requirements</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">-</div>
              </CardContent>
            </Card>
          );
        }

        if (complianceFieldKeys.length === 0) {
          return (
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Compliance & Certification</CardTitle>
                <CardDescription>No compliance fields returned for this valve type</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground italic">
                  The ML prediction did not return any compliance fields for this VDS number.
                </div>
              </CardContent>
            </Card>
          );
        }

        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Code & Compliance</CardTitle>
                <CardDescription>Regulatory and certification requirements</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {activeFields.has("fire_rating") && (
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Fire Safe Rating
                    </Label>
                    <div className="p-3 bg-muted/30 border rounded-md text-sm">
                      {mlData["fire_rating"] || "-"}
                    </div>
                  </div>
                )}
                {activeFields.has("material_certification") && (
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Material Certification
                    </Label>
                    <div className="p-3 bg-muted/30 border rounded-md text-sm">
                      {mlData["material_certification"] || "-"}
                    </div>
                  </div>
                )}
                {activeFields.has("sour_service") && (
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Sour Service Requirements
                    </Label>
                    <div className="p-3 bg-muted/30 border rounded-md text-sm">
                      {mlData["sour_service"] || "-"}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="border-border">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Marking & Finish</CardTitle>
                <CardDescription>Tag and manufacturer marking</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {activeFields.has("marking_purchaser") && (
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <p className="text-sm font-medium mb-1">Purchaser's Specification</p>
                    <p className="text-xs text-muted-foreground">
                      {mlData["marking_purchaser"] || "-"}
                    </p>
                  </div>
                )}
                {activeFields.has("marking_manufacturer") && (
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <p className="text-sm font-medium mb-1">Manufacturer Marking</p>
                    <p className="text-xs text-muted-foreground">
                      {mlData["marking_manufacturer"] || "-"}
                    </p>
                  </div>
                )}
                {activeFields.has("finish") && (
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <p className="text-sm font-medium mb-1">Finish Specification</p>
                    <p className="text-xs text-muted-foreground">
                      {mlData["finish"] || "-"}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        );
      }

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
                      ML Prediction
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
                  {isDataLoaded && ` • ${activeFields.size} fields • ${completionPercentage.toFixed(0)}% complete`}
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
                Enter a VDS number (e.g., <code className="bg-muted px-1 rounded">BSFA1R</code>) to auto-populate fields using ML prediction.
                Only valve-type-specific fields will be shown.
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
