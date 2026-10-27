"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Sparkles,
  User,
  AlertCircle,
  CheckCircle2,
  Calendar,
  Stethoscope,
  Clock,
  Mail,
  MapPin,
  Phone,
  ShieldCheck,
  ChevronRight,
  Lock,
  ChevronDown,
  ChevronUp
} from "lucide-react";

interface SlotInfo {
  start_time: string;
  end_time: string;
  duration_mins: number;
  is_booked: boolean;
  booked_info?: {
    patient_name: string;
    service: string;
  };
}

interface DoctorSlotData {
  doctor_id: string;
  doctor_name: string;
  specialty: string;
  cabin: string;
  color: string;
  is_working_today: boolean;
  working_hours: string;
  slots: SlotInfo[];
}

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Array<{ title: string; source: string; score: number }>;
  leadCaptured?: any;
  handoff?: boolean;
  schedulingCard?: any;
  appointmentConfirmed?: any;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello and welcome to BrightSmile Health & Dental Clinic! I am your clinical front-desk assistant. Based on your symptoms or treatment need, I can triage your care to the right specialist doctor, show their real-time 30-minute schedule, and reserve your consultation pass. You can either use the interactive booking card inside this chat or simply type your details naturally!",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // In-Chat Clinical Intake & Scheduling Card State
  const [showBookingForm, setShowBookingForm] = useState(true);
  const [selectedSeverity, setSelectedSeverity] = useState<"urgent" | "orthodontic" | "cosmetic" | "routine">("routine");
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>("doc-sarah");
  const [selectedDate, setSelectedDate] = useState<string>("2026-10-31");
  const [selectedSlotTime, setSelectedSlotTime] = useState<string>("");
  const [doctorScheduleList, setDoctorScheduleList] = useState<DoctorSlotData[]>([]);
  const [loadingSlots, setLoadingSlots] = useState<boolean>(false);

  // Patient Intake Form Inputs
  const [patientName, setPatientName] = useState("");
  const [patientPhone, setPatientPhone] = useState("");
  const [patientEmail, setPatientEmail] = useState("");
  const [patientLocation, setPatientLocation] = useState("");
  const [patientSymptoms, setPatientSymptoms] = useState("");
  const [bookingInProgress, setBookingInProgress] = useState(false);
  const [bookingSuccessData, setBookingSuccessData] = useState<any>(null);
  const [bookingError, setBookingError] = useState<string | null>(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, showBookingForm]);

  // Fetch live doctor schedules when selectedDate changes
  const fetchLiveSchedule = async (targetDate: string) => {
    setLoadingSlots(true);
    try {
      const res = await fetch(`/api/proxy/v1/schedule/slots?date=${targetDate}`);
      if (res.ok) {
        const data = await res.json();
        if (data.doctors && Array.isArray(data.doctors)) {
          setDoctorScheduleList(data.doctors);
        }
      }
    } catch (e) {
      console.error("Failed to load doctor slots:", e);
    } finally {
      setLoadingSlots(false);
    }
  };

  useEffect(() => {
    fetchLiveSchedule(selectedDate);
  }, [selectedDate]);

  // Handle severity selection and recommend matched doctor
  const handleSelectSeverity = (sev: "urgent" | "orthodontic" | "cosmetic" | "routine") => {
    setSelectedSeverity(sev);
    setSelectedSlotTime("");
    if (sev === "urgent") {
      setSelectedDoctorId("doc-sarah");
      setPatientSymptoms("Severe toothache / Acute pain");
    } else if (sev === "orthodontic") {
      setSelectedDoctorId("doc-alex");
      setPatientSymptoms("Invisalign / Clear Aligner scan");
    } else if (sev === "cosmetic") {
      setSelectedDoctorId("doc-priya");
      setPatientSymptoms("Teeth Whitening / Smile restoration");
    } else {
      setSelectedDoctorId("doc-sarah");
      setPatientSymptoms("Routine 30-min dental checkup & cleaning");
    }
  };

  // Submit direct booking through interactive form
  const handleDirectBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    setBookingError(null);

    if (!selectedSlotTime) {
      setBookingError("Please select an available 30-minute time slot pill from the schedule.");
      return;
    }
    if (!patientName.trim()) {
      setBookingError("Please enter your Full Name.");
      return;
    }
    if (!patientPhone.trim()) {
      setBookingError("Please enter your Mobile / Phone Number.");
      return;
    }
    if (!patientEmail.trim() || !patientEmail.includes("@")) {
      setBookingError("Please enter a valid Email Address for your confirmation pass.");
      return;
    }
    if (!patientLocation.trim()) {
      setBookingError("Please enter your City / Location so we can route clinic logistics.");
      return;
    }

    setBookingInProgress(true);
    try {
      const res = await fetch("/api/proxy/v1/schedule/appointments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doctor_id: selectedDoctorId,
          patient_name: patientName.trim(),
          patient_phone: patientPhone.trim(),
          patient_email: patientEmail.trim(),
          patient_location: patientLocation.trim(),
          appointment_date: selectedDate,
          start_time: selectedSlotTime,
          duration_mins: 30,
          service_type: patientSymptoms || `${selectedSeverity.toUpperCase()} Dental Consultation`,
          notes: `Booked via In-Chat Intake Form. Location: ${patientLocation.trim()}. Severity: ${selectedSeverity}`
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setBookingSuccessData(data);
        // Add confirmation message to chat stream
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `🎉 Excellent! Your 30-minute clinical appointment has been confirmed with ${data.doctor_name} on ${selectedDate} at ${selectedSlotTime} (${data.cabin}).\n\nDual notifications dispatched:\n1. Dedicated Hospital Intake Alert sent to prahaashnms18@gmail.com with your location (${patientLocation.trim()}).\n2. Patient Appointment Pass sent directly to ${patientEmail.trim()}.`,
            appointmentConfirmed: data,
          },
        ]);
        // Refresh schedule to reflect newly booked slot immediately
        fetchLiveSchedule(selectedDate);
      } else {
        setBookingError(data.detail?.message || "Failed to reserve slot. It may have been just booked by another patient.");
      }
    } catch (err: any) {
      setBookingError("Network error while submitting reservation. Please try again.");
    } finally {
      setBookingInProgress(false);
    }
  };

  // Conversational AI messaging (User types naturally in AI chat)
  const sendMessage = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/proxy/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          channel: "web",
          tenant: "brightsmile",
          conversation_id: conversationId,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.conversation_id && !conversationId) {
          setConversationId(data.conversation_id);
        }

        // If AI detected symptoms or scheduling, update interactive form state too!
        if (data.scheduling_card) {
          if (data.scheduling_card.severity) {
            setSelectedSeverity(data.scheduling_card.severity);
          }
          if (data.scheduling_card.recommended_doctor_ids?.[0]) {
            setSelectedDoctorId(data.scheduling_card.recommended_doctor_ids[0]);
          }
        }

        const asstMsg: Message = {
          role: "assistant",
          content: data.answer,
          citations: data.citations,
          leadCaptured: data.lead_captured,
          handoff: data.handoff,
          schedulingCard: data.scheduling_card
        };
        setMessages((prev) => [...prev, asstMsg]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Sorry, I encountered an issue connecting to our practice scheduling engine. Please try again or call our desk at (555) 019-2831.",
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Network error connecting to clinic service. Please ensure connectivity.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const activeDoctorData = doctorScheduleList.find((d) => d.doctor_id === selectedDoctorId);

  return (
    <div className="flex-1 flex flex-col h-full max-w-5xl mx-auto w-full p-2 sm:p-5 overflow-hidden">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200/80 bg-white/95 backdrop-blur-xs px-3 sm:px-5 py-2.5 rounded-2xl border border-slate-200/60 shadow-2xs shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 shadow-2xs">
            <Stethoscope className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base sm:text-lg font-black text-slate-900 tracking-tight">
                BrightSmile Front Desk & Doctor Triage
              </h1>
              <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-[10px] font-bold">
                Severity Matching
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              Clinical doctor schedules, interactive slot selection & dual intake notification
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowBookingForm(!showBookingForm)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold transition-all shadow-2xs"
          >
            <Calendar className="h-3.5 w-3.5" />
            <span>{showBookingForm ? "Hide Doctor Widget" : "Show Doctor Widget"}</span>
            {showBookingForm ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>
        </div>
      </div>

      {/* Main Container: Chat on Left, Embedded Interactive Scheduling & Intake Card */}
      <div className="flex-1 overflow-y-auto py-3 space-y-4 px-1">
        {/* Messages Stream */}
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex gap-3 max-w-3xl ${
              m.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
            }`}
          >
            {/* Avatar */}
            <div
              className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold shadow-2xs ${
                m.role === "user"
                  ? "bg-teal-600 text-white"
                  : "bg-white text-teal-700 border border-slate-200"
              }`}
            >
              {m.role === "user" ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
            </div>

            <div className="space-y-2 w-full max-w-2xl">
              {/* Message Bubble */}
              <div
                className={`p-3.5 sm:p-4 rounded-2xl text-sm leading-relaxed shadow-2xs whitespace-pre-line ${
                  m.role === "user"
                    ? "bg-teal-600 text-white rounded-tr-none"
                    : "bg-white border border-slate-200 text-slate-800 rounded-tl-none font-sans"
                }`}
              >
                {m.content}
              </div>

              {/* Lead Capture Alert Banner */}
              {m.leadCaptured && (
                <div className="p-3.5 rounded-xl bg-teal-50 border border-teal-200/90 text-xs text-teal-900 space-y-1.5 shadow-2xs">
                  <div className="flex items-center gap-2 font-bold text-teal-950">
                    <CheckCircle2 className="h-4 w-4 text-teal-600 shrink-0" />
                    <span>Intake Notification Dispatched:</span>
                  </div>
                  <div className="space-y-1 pl-6 text-[11px] text-teal-800">
                    <div className="flex items-center gap-1.5">
                      <Mail className="h-3 w-3 text-teal-600" />
                      <span><strong>Hospital Intake:</strong> Alert delivered to practice inbox at <code>prahaashnms18@gmail.com</code> (Only Hospital Copy)</span>
                    </div>
                    {m.leadCaptured.location && (
                      <div className="flex items-center gap-1.5">
                        <MapPin className="h-3 w-3 text-teal-600" />
                        <span><strong>Patient Location:</strong> {m.leadCaptured.location}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Appointment Confirmed Banner */}
              {m.appointmentConfirmed && (
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-950 space-y-2 shadow-2xs">
                  <div className="flex items-center gap-2 font-bold text-emerald-900 text-sm">
                    <ShieldCheck className="h-5 w-5 text-emerald-600 shrink-0" />
                    <span>Official Consultation Confirmed!</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-emerald-800 pt-1">
                    <div><strong>Doctor:</strong> {m.appointmentConfirmed.doctor_name}</div>
                    <div><strong>Location / Cabin:</strong> {m.appointmentConfirmed.cabin}</div>
                    <div><strong>Time Slot:</strong> {m.appointmentConfirmed.time_slot} ({m.appointmentConfirmed.appointment_date})</div>
                    <div><strong>Duration:</strong> 30 Minutes Consultation</div>
                  </div>
                </div>
              )}

              {/* Human Handoff Banner */}
              {m.handoff && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 text-amber-600" />
                  <div>
                    <span className="font-semibold">Front-Desk Team Alerted: </span>
                    Our receptionist staff has been paged via Telegram and will follow up with you.
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Embedded Interactive Clinical Booking & Triage Card */}
        {showBookingForm && (
          <div className="my-4 p-4 sm:p-5 rounded-2xl bg-white border-2 border-teal-500/30 shadow-md transition-all">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="h-7 w-7 rounded-lg bg-teal-600 text-white flex items-center justify-center font-bold text-xs">
                  <Calendar className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-extrabold text-slate-900">
                    Clinical Booking & Doctor Schedule
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Select by clinical severity, choose open 30-min time pills, or enter intake details below
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                Live DB Connected
              </span>
            </div>

            {/* Step 1: Severity Triage Selector */}
            <div className="mt-3">
              <label className="text-xs font-bold text-slate-700 block mb-1.5">
                Step 1: Clinical Need & Severity Triage
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <button
                  type="button"
                  onClick={() => handleSelectSeverity("urgent")}
                  className={`p-2.5 rounded-xl border text-left transition-all text-xs font-semibold ${
                    selectedSeverity === "urgent"
                      ? "bg-red-50 border-red-400 text-red-900 shadow-2xs"
                      : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  <div className="text-sm">🚨 Urgent / Pain</div>
                  <div className="text-[10px] text-slate-500 font-normal mt-0.5">Toothache, Trauma, Swelling</div>
                </button>

                <button
                  type="button"
                  onClick={() => handleSelectSeverity("orthodontic")}
                  className={`p-2.5 rounded-xl border text-left transition-all text-xs font-semibold ${
                    selectedSeverity === "orthodontic"
                      ? "bg-sky-50 border-sky-400 text-sky-900 shadow-2xs"
                      : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  <div className="text-sm">🦷 Orthodontics</div>
                  <div className="text-[10px] text-slate-500 font-normal mt-0.5">Invisalign, Aligners, Braces</div>
                </button>

                <button
                  type="button"
                  onClick={() => handleSelectSeverity("cosmetic")}
                  className={`p-2.5 rounded-xl border text-left transition-all text-xs font-semibold ${
                    selectedSeverity === "cosmetic"
                      ? "bg-emerald-50 border-emerald-400 text-emerald-900 shadow-2xs"
                      : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  <div className="text-sm">✨ Cosmetic</div>
                  <div className="text-[10px] text-slate-500 font-normal mt-0.5">Whitening, Veneers, Smile</div>
                </button>

                <button
                  type="button"
                  onClick={() => handleSelectSeverity("routine")}
                  className={`p-2.5 rounded-xl border text-left transition-all text-xs font-semibold ${
                    selectedSeverity === "routine"
                      ? "bg-teal-50 border-teal-400 text-teal-900 shadow-2xs"
                      : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  <div className="text-sm">🩺 Routine / General</div>
                  <div className="text-[10px] text-slate-500 font-normal mt-0.5">Checkup, Cleaning, Cavity</div>
                </button>
              </div>
            </div>

            {/* Step 2: Doctor & Date Selection */}
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1.5">
                  Step 2: Recommended Doctor on Duty
                </label>
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {doctorScheduleList.map((doc) => {
                    const isSelected = selectedDoctorId === doc.doctor_id;
                    return (
                      <div
                        key={doc.doctor_id}
                        onClick={() => {
                          setSelectedDoctorId(doc.doctor_id);
                          setSelectedSlotTime("");
                        }}
                        className={`p-2.5 rounded-xl border cursor-pointer transition-all flex items-center justify-between text-xs ${
                          isSelected
                            ? "bg-teal-50 border-teal-500 text-teal-950 font-bold shadow-2xs"
                            : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <div
                            className="h-3 w-3 rounded-full shrink-0"
                            style={{ backgroundColor: doc.color || "#0d9488" }}
                          />
                          <div>
                            <div>{doc.doctor_name}</div>
                            <div className="text-[10px] text-slate-500 font-normal">{doc.specialty} • {doc.cabin}</div>
                          </div>
                        </div>
                        <div className="text-[10px] text-slate-500 font-medium">
                          {doc.working_hours}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1.5">
                  Select Consultation Date
                </label>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => {
                    setSelectedDate(e.target.value);
                    setSelectedSlotTime("");
                  }}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-teal-500"
                />
                <div className="flex items-center gap-1.5 mt-2 overflow-x-auto text-[11px]">
                  <span className="text-slate-400">Presets:</span>
                  <button
                    type="button"
                    onClick={() => setSelectedDate("2026-10-31")}
                    className="px-2 py-0.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 whitespace-nowrap font-medium"
                  >
                    Sat Oct 31
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedDate("2026-11-02")}
                    className="px-2 py-0.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 whitespace-nowrap font-medium"
                  >
                    Mon Nov 02
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedDate("2026-11-03")}
                    className="px-2 py-0.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 whitespace-nowrap font-medium"
                  >
                    Tue Nov 03
                  </button>
                </div>

                <div className="mt-3 p-2 rounded-lg bg-teal-50/70 border border-teal-100 text-[11px] text-teal-900">
                  <strong>30-Min Rule:</strong> Strict overlap prevention in database. Double-booking the same doctor at the same time is prohibited.
                </div>
              </div>
            </div>

            {/* Step 3: Interactive 30-Minute Time Slot Pills */}
            <div className="mt-4 pt-3 border-t border-slate-100">
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-slate-700">
                  Step 3: Select Available 30-Min Slot Pill ({selectedDate})
                </label>
                {loadingSlots && (
                  <span className="text-[11px] text-teal-600 animate-pulse">Loading live slots...</span>
                )}
              </div>

              {activeDoctorData ? (
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                  {activeDoctorData.slots.map((slot, sIdx) => {
                    const isSelected = selectedSlotTime === slot.start_time;
                    if (slot.is_booked) {
                      return (
                        <div
                          key={sIdx}
                          title={`Reserved by ${slot.booked_info?.patient_name || 'Existing Patient'}`}
                          className="p-2 rounded-xl bg-slate-100 border border-slate-200 text-slate-400 text-center text-xs flex flex-col items-center justify-center cursor-not-allowed opacity-80"
                        >
                          <div className="flex items-center gap-1 font-semibold">
                            <Lock className="h-2.5 w-2.5" />
                            <span>{slot.start_time}</span>
                          </div>
                          <span className="text-[9px] uppercase tracking-wider text-rose-500 font-bold">Reserved</span>
                        </div>
                      );
                    }

                    return (
                      <button
                        key={sIdx}
                        type="button"
                        onClick={() => setSelectedSlotTime(slot.start_time)}
                        className={`p-2 rounded-xl border text-center transition-all text-xs font-bold ${
                          isSelected
                            ? "bg-teal-600 text-white border-teal-600 shadow-xs scale-102"
                            : "bg-white hover:bg-teal-50 border-slate-200 text-slate-800 hover:border-teal-400"
                        }`}
                      >
                        <div>{slot.start_time}</div>
                        <div className={`text-[9px] font-normal ${isSelected ? "text-teal-100" : "text-emerald-600"}`}>
                          30 mins
                        </div>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="p-3 text-xs text-slate-500 text-center bg-slate-50 rounded-xl">
                  {loadingSlots ? "Querying clinic schedule database..." : "No doctor working hours found for this day."}
                </div>
              )}
            </div>

            {/* Step 4: Patient Intake Details Form */}
            <form onSubmit={handleDirectBooking} className="mt-4 pt-3 border-t border-slate-100">
              <label className="text-xs font-bold text-slate-700 block mb-2">
                Step 4: Patient Intake Details (Both Form Submission & AI Typing Supported)
              </label>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                <div>
                  <input
                    type="text"
                    required
                    placeholder="Patient Full Name *"
                    value={patientName}
                    onChange={(e) => setPatientName(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-teal-500"
                  />
                </div>

                <div>
                  <input
                    type="tel"
                    required
                    placeholder="Mobile / Phone Number *"
                    value={patientPhone}
                    onChange={(e) => setPatientPhone(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-teal-500"
                  />
                </div>

                <div>
                  <input
                    type="email"
                    required
                    placeholder="Email ID (For Patient Receipt Copy) *"
                    value={patientEmail}
                    onChange={(e) => setPatientEmail(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-teal-500"
                  />
                </div>

                <div>
                  <input
                    type="text"
                    required
                    placeholder="Patient Location / City / Neighborhood *"
                    value={patientLocation}
                    onChange={(e) => setPatientLocation(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div className="mt-2.5">
                <input
                  type="text"
                  placeholder="Primary Symptoms / Treatment Interest (Optional)"
                  value={patientSymptoms}
                  onChange={(e) => setPatientSymptoms(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-teal-500"
                />
              </div>

              {bookingError && (
                <div className="mt-2.5 p-2 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{bookingError}</span>
                </div>
              )}

              <div className="mt-3 flex items-center justify-between gap-3">
                <div className="text-[11px] text-slate-500 hidden sm:block">
                  ⚡ <strong>Dual Email Guarantee:</strong> Hospital copy &rarr; <code>prahaashnms18@gmail.com</code> | Patient copy &rarr; <code>{patientEmail || "Patient's email"}</code>
                </div>

                <button
                  type="submit"
                  disabled={bookingInProgress || !selectedSlotTime}
                  className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-bold text-xs flex items-center gap-2 transition-all shadow-xs ml-auto"
                >
                  {bookingInProgress ? (
                    <>
                      <Sparkles className="h-3.5 w-3.5 animate-spin" />
                      <span>Reserving Slot...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      <span>Confirm 30-Min Consultation</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}

        {loading && (
          <div className="flex gap-3 max-w-md mr-auto">
            <div className="h-8 w-8 rounded-full bg-white border border-slate-200 text-teal-600 flex items-center justify-center shrink-0">
              <Sparkles className="h-4 w-4 animate-spin" />
            </div>
            <div className="p-3.5 rounded-2xl bg-white border border-slate-200 text-xs text-slate-500 flex items-center gap-2 shadow-2xs">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500 animate-pulse"></span>
              <span>Checking live doctor schedules, severity rules & knowledge base...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Slot Quick Inquire Pills */}
      <div className="py-2 flex items-center gap-2 overflow-x-auto text-xs pb-2 shrink-0">
        <span className="text-slate-400 font-semibold whitespace-nowrap text-[11px] uppercase tracking-wider">
          Quick Inquire:
        </span>
        <button
          onClick={() => sendMessage("I have severe tooth pain on my lower left jaw, please triage me.")}
          className="px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-red-400 hover:bg-red-50 text-slate-700 hover:text-red-900 whitespace-nowrap transition-all shadow-2xs font-medium"
        >
          🚨 Severe Tooth Pain
        </button>
        <button
          onClick={() => sendMessage("Do you have Saturday 11 AM available for Dr. Sarah Mitchell?")}
          className="px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-teal-400 hover:bg-teal-50 text-slate-700 hover:text-teal-900 whitespace-nowrap transition-all shadow-2xs font-medium"
        >
          📅 Saturday 11:00 AM Slot
        </button>
        <button
          onClick={() => sendMessage("Can I book Saturday 11:30 AM with Dr. Sarah? My name is John, location Midtown.")}
          className="px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-teal-400 hover:bg-teal-50 text-slate-700 hover:text-teal-900 whitespace-nowrap transition-all shadow-2xs font-medium"
        >
          📅 Saturday 11:30 AM Slot
        </button>
        <button
          onClick={() => sendMessage("I want Invisalign with Dr. Alex Rivera, what are his consultation days?")}
          className="px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-sky-400 hover:bg-sky-50 text-slate-700 hover:text-sky-900 whitespace-nowrap transition-all shadow-2xs font-medium"
        >
          🦷 Invisalign Scan ($4,200)
        </button>
      </div>

      {/* AI Chatbox Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
        className="flex items-center gap-2 pt-2 border-t border-slate-200/80 shrink-0"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type naturally or enter details (e.g. Saturday 11:30 AM, John Doe, 555-019-3321, john@example.com, Downtown)..."
          className="flex-1 bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-teal-500 shadow-2xs transition-colors"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-5 py-3 rounded-xl bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-semibold text-sm flex items-center gap-2 transition-all shadow-xs"
        >
          <span>Send</span>
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
