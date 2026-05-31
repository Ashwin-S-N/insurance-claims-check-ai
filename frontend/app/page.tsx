"use client";

import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  ClipboardCheck,
  FileCheck2,
  IndianRupee,
  Play,
  RotateCcw,
  Send,
  ShieldAlert,
  Workflow,
  XCircle
} from "lucide-react";
import { useMemo, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const demoClaims = {
  cleanApproval: {
    member_id: "EMP001",
    policy_id: "PLUM_GHI_2024",
    claim_category: "CONSULTATION",
    treatment_date: "2024-11-01",
    claimed_amount: 1500,
    ytd_claims_amount: 5000,
    documents: [
      {
        file_id: "F007",
        actual_type: "PRESCRIPTION",
        content: {
          doctor_name: "Dr. Arun Sharma",
          doctor_registration: "KA/45678/2015",
          patient_name: "Rajesh Kumar",
          diagnosis: "Viral Fever",
          medicines: ["Paracetamol 650mg"]
        }
      },
      {
        file_id: "F008",
        actual_type: "HOSPITAL_BILL",
        content: {
          hospital_name: "City Clinic, Bengaluru",
          patient_name: "Rajesh Kumar",
          line_items: [
            { description: "Consultation Fee", amount: 1000 },
            { description: "CBC Test", amount: 300 },
            { description: "Dengue NS1 Test", amount: 200 }
          ],
          total: 1500
        }
      }
    ]
  },
  earlyStop: {
    member_id: "EMP001",
    policy_id: "PLUM_GHI_2024",
    claim_category: "CONSULTATION",
    treatment_date: "2024-11-01",
    claimed_amount: 1500,
    documents: [
      { file_id: "F001", file_name: "dr_sharma_prescription.jpg", actual_type: "PRESCRIPTION" },
      { file_id: "F002", file_name: "another_prescription.jpg", actual_type: "PRESCRIPTION" }
    ]
  },
  fraudReview: {
    member_id: "EMP008",
    policy_id: "PLUM_GHI_2024",
    claim_category: "CONSULTATION",
    treatment_date: "2024-10-30",
    claimed_amount: 4800,
    claims_history: [
      { claim_id: "CLM_0081", date: "2024-10-30", amount: 1200, provider: "City Clinic A" },
      { claim_id: "CLM_0082", date: "2024-10-30", amount: 1800, provider: "City Clinic B" },
      { claim_id: "CLM_0083", date: "2024-10-30", amount: 2100, provider: "Wellness Center" }
    ],
    documents: [
      { file_id: "F017", actual_type: "PRESCRIPTION", content: { diagnosis: "Migraine", doctor_name: "Dr. S. Khan" } },
      { file_id: "F018", actual_type: "HOSPITAL_BILL", content: { total: 4800 } }
    ]
  }
};

type ApiResponse = {
  claim_id: string;
  stopped_early: boolean;
  message: string;
  decision: string | null;
  approved_amount: number;
  confidence_score: number;
  rejection_reasons: string[];
  fraud_score?: number | null;
  fraud_signals: string[];
  line_item_results: Array<Record<string, unknown>>;
  trace: Array<{ step: string; status: string; message: string; data: Record<string, unknown> }>;
  extracted?: Record<string, unknown> | null;
};

const statusStyles: Record<string, string> = {
  PASS: "border-emerald-200 bg-emerald-50 text-emerald-800",
  FAIL: "border-red-200 bg-red-50 text-red-800",
  WARN: "border-amber-200 bg-amber-50 text-amber-800",
  INFO: "border-sky-200 bg-sky-50 text-sky-800",
  SKIPPED: "border-stone-200 bg-stone-100 text-stone-700"
};

const decisionStyles: Record<string, string> = {
  APPROVED: "bg-emerald-600 text-white",
  PARTIAL: "bg-amber-500 text-white",
  REJECTED: "bg-red-600 text-white",
  MANUAL_REVIEW: "bg-indigo-600 text-white"
};

export default function Home() {
  const [payload, setPayload] = useState(JSON.stringify(demoClaims.cleanApproval, null, 2));
  const [response, setResponse] = useState<ApiResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const parsed = useMemo(() => {
    try {
      return JSON.parse(payload);
    } catch {
      return null;
    }
  }, [payload]);

  async function submitClaim() {
    setLoading(true);
    setError("");
    setResponse(null);
    try {
      if (!parsed) throw new Error("Claim JSON is invalid.");
      const res = await fetch(`${API_BASE}/claims`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed)
      });
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      setResponse(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-page text-ink">
      <header className="border-b border-stone-200 bg-white/95 shadow-sm">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-md bg-plum text-white shadow-sm">
              <Workflow className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-plum">Plum Insurance Claim Check</p>
              <h1 className="text-2xl font-semibold tracking-normal text-ink">Claims Processing Console</h1>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center text-xs sm:min-w-[360px]">
            <HeaderStat label="Agents" value="6" />
            <HeaderStat label="Eval Cases" value="12/12" />
            <HeaderStat label="Trace" value="Visible" />
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-4">
          <section className="panel">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold">Claim Intake</h2>
                <p className="mt-1 text-sm text-stone-600">Paste an input to check the claim status (in .json format)</p>
              </div>
              <span className={`rounded-md px-3 py-1.5 text-xs font-semibold ${parsed ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
                {parsed ? "Valid JSON" : "Invalid JSON"}
              </span>
            </div>

            <div className="grid gap-2 sm:grid-cols-3">
              <ScenarioButton icon={<FileCheck2 className="h-4 w-4" />} title="Approval" detail="Clean payable claim" onClick={() => setPayload(JSON.stringify(demoClaims.cleanApproval, null, 2))} active={!response} />
              <ScenarioButton icon={<ShieldAlert className="h-4 w-4" />} title="Early Stop" detail="Wrong documents" onClick={() => setPayload(JSON.stringify(demoClaims.earlyStop, null, 2))} />
              <ScenarioButton icon={<Play className="h-4 w-4" />} title="Fraud Review" detail="Same-day signals" onClick={() => setPayload(JSON.stringify(demoClaims.fraudReview, null, 2))} />
            </div>

            <label className="mt-5 block text-sm font-medium text-stone-700" htmlFor="claim-json">Claim submission JSON</label>
            <textarea
              id="claim-json"
              value={payload}
              onChange={(event) => setPayload(event.target.value)}
              className="mt-2 h-[560px] w-full resize-none rounded-md border border-stone-300 bg-code p-4 font-mono text-sm leading-6 text-stone-100 outline-none shadow-inner focus:border-plum focus:ring-2 focus:ring-plum/25"
              spellCheck={false}
            />
            <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto]">
              <button onClick={submitClaim} disabled={loading || !parsed} className="inline-flex items-center justify-center gap-2 rounded-md bg-plum px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-plumDark disabled:cursor-not-allowed disabled:bg-stone-400">
                <Send className="h-4 w-4" /> {loading ? "Processing claim..." : "Submit claim"}
              </button>
              <button title="Reset response" onClick={() => { setResponse(null); setError(""); }} className="inline-flex items-center justify-center gap-2 rounded-md bg-white px-4 py-3 text-sm font-semibold text-ink ring-1 ring-stone-300 transition hover:bg-stone-50">
                <RotateCcw className="h-4 w-4" /> Reset
              </button>
            </div>
            {error && <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          </section>
        </div>

        <div className="space-y-4">
          <DecisionPanel response={response} />
          <TracePanel response={response} />
        </div>
      </section>
    </main>
  );
}

function HeaderStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-stone-200 bg-stone-50 px-3 py-2">
      <p className="text-[11px] font-medium uppercase text-stone-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}

function ScenarioButton({ icon, title, detail, onClick, active = false }: { icon: React.ReactNode; title: string; detail: string; onClick: () => void; active?: boolean }) {
  return (
    <button onClick={onClick} className={`rounded-md border p-3 text-left transition hover:-translate-y-0.5 hover:shadow-sm ${active ? "border-plum bg-plumSoft" : "border-stone-200 bg-white hover:border-plum/50"}`}>
      <div className="flex items-center gap-2 text-sm font-semibold text-ink">
        <span className="flex h-8 w-8 items-center justify-center rounded-md bg-white text-plum ring-1 ring-stone-200">{icon}</span>
        {title}
      </div>
      <p className="mt-2 text-xs text-stone-600">{detail}</p>
    </button>
  );
}

function DecisionPanel({ response }: { response: ApiResponse | null }) {
  if (!response) {
    return (
      <section className="panel overflow-hidden">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-md bg-plumSoft text-plum">
            <ClipboardCheck className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Decision Review</h2>
            <p className="mt-1 text-sm leading-6 text-stone-600">Submit a claim to see the final decision, approved amount, confidence score, fraud signals, and full audit trace.</p>
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <Metric label="Decision" value="Pending" />
          <Metric label="Approved" value="-" />
          <Metric label="Confidence" value="-" />
        </div>
      </section>
    );
  }

  const decision = response.decision || "STOPPED EARLY";
  const badgeClass = response.decision ? decisionStyles[response.decision] || "bg-stone-700 text-white" : "bg-red-600 text-white";

  return (
    <section className="panel overflow-hidden">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">{response.claim_id}</p>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <span className={`rounded-md px-3 py-2 text-sm font-semibold ${badgeClass}`}>{decision}</span>
            {response.stopped_early && <span className="rounded-md bg-red-50 px-3 py-2 text-xs font-semibold text-red-700">Pipeline stopped before adjudication</span>}
          </div>
        </div>
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-right">
          <p className="text-xs font-medium text-emerald-700">Approved Amount</p>
          <p className="mt-1 flex items-center justify-end gap-1 text-2xl font-semibold text-emerald-900">
            <IndianRupee className="h-5 w-5" /> {response.approved_amount.toLocaleString("en-IN")}
          </p>
        </div>
      </div>

      <p className="mt-5 rounded-md border border-stone-200 bg-stone-50 p-4 text-sm leading-6 text-stone-700">{response.message}</p>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Metric label="Confidence" value={`${Math.round(response.confidence_score * 100)}%`} />
        <Metric label="Fraud Score" value={response.fraud_score == null ? "-" : response.fraud_score.toFixed(2)} />
        <Metric label="Stopped Early" value={response.stopped_early ? "Yes" : "No"} />
      </div>

      {(response.rejection_reasons.length > 0 || response.fraud_signals.length > 0) && (
        <div className="mt-4 space-y-2 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {[...response.rejection_reasons, ...response.fraud_signals].map((item) => <div key={item} className="flex gap-2"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> <span>{item}</span></div>)}
        </div>
      )}

      {response.line_item_results.length > 0 && (
        <pre className="mt-4 max-h-56 overflow-auto rounded-md bg-code p-3 text-xs leading-5 text-stone-100">{JSON.stringify(response.line_item_results, null, 2)}</pre>
      )}
    </section>
  );
}

function TracePanel({ response }: { response: ApiResponse | null }) {
  if (!response) {
    return (
      <section className="panel">
        <div className="flex items-center gap-3">
          <Activity className="h-5 w-5 text-plum" />
          <h2 className="text-lg font-semibold">Agent Steps</h2>
        </div>
        <div className="mt-5 space-y-3">
          {["Document verification", "Extraction", "Policy engine", "Fraud detection", "Decision"].map((step) => (
            <div key={step} className="flex items-center gap-3 rounded-md border border-dashed border-stone-300 bg-stone-50 p-3 text-sm text-stone-500">
              <CircleDot className="h-4 w-4" />
              {step}
            </div>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Activity className="h-5 w-5 text-plum" />
          <h2 className="text-lg font-semibold">Agent Steps</h2>
        </div>
        <span className="rounded-md bg-stone-100 px-3 py-1.5 text-xs font-semibold text-stone-600">{response.trace.length} events</span>
      </div>
      <div className="mt-5 space-y-3">
        {response.trace.map((event, index) => (
          <TraceEventCard key={`${event.step}-${index}`} event={event} index={index} />
        ))}
      </div>
      {response.extracted && <pre className="mt-4 max-h-72 overflow-auto rounded-md bg-code p-3 text-xs leading-5 text-stone-100">{JSON.stringify(response.extracted, null, 2)}</pre>}
    </section>
  );
}

function TraceEventCard({ event, index }: { event: ApiResponse["trace"][number]; index: number }) {
  return (
    <div className="grid grid-cols-[36px_1fr] gap-3">
      <div className="flex flex-col items-center">
        <div className={`flex h-9 w-9 items-center justify-center rounded-md border ${statusStyles[event.status] || statusStyles.INFO}`}>
          <StatusIcon status={event.status} />
        </div>
        <div className="mt-2 h-full min-h-6 w-px bg-stone-200" />
      </div>
      <div className="rounded-md border border-stone-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-400">Step {index + 1}</p>
            <h3 className="mt-1 text-sm font-semibold text-ink">{event.step.replace(/_/g, " ")}</h3>
          </div>
          <span className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${statusStyles[event.status] || statusStyles.INFO}`}>{event.status}</span>
        </div>
        <p className="mt-3 text-sm leading-6 text-stone-700">{event.message}</p>
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === "PASS") return <CheckCircle2 className="h-4 w-4" />;
  if (status === "FAIL") return <XCircle className="h-4 w-4" />;
  if (status === "WARN") return <AlertTriangle className="h-4 w-4" />;
  return <CircleDot className="h-4 w-4" />;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-stone-200 bg-white p-3">
      <p className="text-xs font-medium uppercase text-stone-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-ink">{value}</p>
    </div>
  );
}
