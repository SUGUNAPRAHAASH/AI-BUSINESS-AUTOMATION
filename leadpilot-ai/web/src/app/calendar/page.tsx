"use client";

import { useEffect, useState } from "react";
import {
  Calendar as CalendarIcon,
  Clock,
  UserCheck,
  AlertCircle,
  Plus,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Shield,
  Stethoscope,
  Sparkles,
  RefreshCw,
  Mail,
  User,
  Settings,
  X,
} from "lucide-react";

interface Doctor {
  id: string;
  name: string;
  title: string;
  specialty: string;
  cabin: string;
  color: string;
  is_active: boolean;
  schedules?: any[];
}

interface SlotInfo {
  start_time: string;
  end_time: string;
  duration_mins: number;
  is_booked: boolean;
  booked_info?: {
    patient_name: string;
    service: string;
    appointment_id: string;
  } | null;
}

interface DoctorDaySlots {
  doctor_id: string;
  doctor_name: string;
  specialty: string;
  cabin: string;
  color: string;
  is_working_today: boolean;
  working_hours?: string;
  slot_duration?: number;
  slots: SlotInfo[];
}

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState<string>("2026-10-31"); // Default Saturday demo
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>("all");
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [scheduleData, setScheduleData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"calendar" | "admin">("calendar");

  // Booking Modal State
  const [bookingModalOpen, setBookingModalOpen] = useState(false);
  const [modalDoctorId, setModalDoctorId] = useState("");
  const [modalTime, setModalTime] = useState("11:00");
  const [modalDuration, setModalDuration] = useState(30);
  const [patientName, setPatientName] = useState("");
  const [patientEmail, setPatientEmail] = useState("");
  const [patientPhone, setPatientPhone] = useState("");
  const [serviceType, setServiceType] = useState("Basic Dental Consultation (30 mins)");
  const [notes, setNotes] = useState("");
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingFeedback, setBookingFeedback] = useState<any>(null);

  // Admin Schedule Settings State
  const [adminSelectedDoc, setAdminSelectedDoc] = useState<string>("");
  const [adminSchedules, setAdminSchedules] = useState<any[]>([]);
  const [savingRoster, setSavingRoster] = useState(false);
  const [rosterSuccess, setRosterSuccess] = useState<string | null>(null);

  // Fetch Doctors and Schedule
  async function loadData() {
    setLoading(true);
    try {
      const [resDocs, resSlots] = await Promise.all([
        fetch("/api/proxy/v1/schedule/doctors"),
        fetch(`/api/proxy/v1/schedule/slots?date=${currentDate}`),
      ]);
      if (resDocs.ok) {
        const dData = await resDocs.json();
        setDoctors(dData.doctors || []);
        if (dData.doctors.length > 0 && !adminSelectedDoc) {
          setAdminSelectedDoc(dData.doctors[0].id);
          setAdminSchedules(dData.doctors[0].schedules || []);
        }
      }
      if (resSlots.ok) {
        const sData = await resSlots.json();
        setScheduleData(sData);
      }
    } catch (err) {
      console.error("Failed to load schedule data", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [currentDate]);

  // Adjust date helper
  const handleDateShift = (days: number) => {
    const cur = new Date(currentDate);
    cur.setDate(cur.getDate() + days);
    const iso = cur.toISOString().split("T")[0];
    setCurrentDate(iso);
  };

  // Open booking modal for a specific doctor & slot
  const handleOpenBooking = (docId: string, time: string) => {
    setModalDoctorId(docId);
    setModalTime(time);
    setBookingFeedback(null);
    setBookingModalOpen(true);
  };

  // Submit new booking with real overlap check
  const handleBookSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientName || !patientEmail) return;

    setBookingLoading(true);
    setBookingFeedback(null);
    try {
      const res = await fetch("/api/proxy/v1/schedule/appointments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doctor_id: modalDoctorId || undefined,
          appointment_date: currentDate,
          start_time: modalTime,
          duration_mins: Number(modalDuration),
          patient_name: patientName,
          patient_email: patientEmail,
          patient_phone: patientPhone,
          service_type: serviceType,
          notes: notes,
        }),
      });

      const resData = await res.json();
      if (res.ok) {
        setBookingFeedback({
          type: "success",
          message: resData.message,
          data: resData,
        });
        await loadData();
      } else {
        setBookingFeedback({
          type: "conflict",
          message: resData.detail?.message || "Time slot conflict",
          alternatives: resData.detail?.alternative_doctors_available_at_same_time || [],
          suggestion: resData.detail?.suggestion,
        });
      }
    } catch (err: any) {
      setBookingFeedback({
        type: "error",
        message: err.message || "Failed to book appointment",
      });
    } finally {
      setBookingLoading(false);
    }
  };

  // Save updated admin roster
  const handleSaveRoster = async () => {
    if (!adminSelectedDoc) return;
    setSavingRoster(true);
    setRosterSuccess(null);
    try {
      const res = await fetch(`/api/proxy/v1/schedule/doctors/${adminSelectedDoc}/roster`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ schedules: adminSchedules }),
      });
      if (res.ok) {
        setRosterSuccess("Doctor roster & working hours updated successfully!");
        await loadData();
      }
    } finally {
      setSavingRoster(false);
    }
  };

  // Cancel appointment to free slot
  const handleCancelAppointment = async (appId: string) => {
    if (!confirm("Are you sure you want to cancel this appointment and reopen the slot?")) return;
    try {
      await fetch(`/api/proxy/v1/schedule/appointments/${appId}`, { method: "DELETE" });
      await loadData();
    } catch (err) {
      console.error("Cancel failed", err);
    }
  };

  const filteredDoctors: DoctorDaySlots[] =
    scheduleData?.doctors?.filter((d: DoctorDaySlots) =>
      selectedDoctorId === "all" ? true : d.doctor_id === selectedDoctorId
    ) || [];

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Top Header & Navigation */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-teal-50 text-teal-700 border border-teal-200">
              Practice Scheduling System
            </span>
            <span className="text-xs text-slate-500 font-medium hidden sm:inline">
              30-Min Consultation Architecture • Multi-Doctor Roster
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mt-1 flex items-center gap-2.5">
            <CalendarIcon className="h-7 w-7 text-teal-600" />
            Appointments & Doctor Schedules
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated conflict prevention, dedicated doctor working hours, and dual email dispatch.
          </p>
        </div>

        {/* Tab Selector & New Booking Button */}
        <div className="flex items-center gap-3">
          <div className="flex p-1 rounded-xl bg-slate-100 border border-slate-200 text-xs font-semibold">
            <button
              onClick={() => setActiveTab("calendar")}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "calendar"
                  ? "bg-white text-teal-800 shadow-xs font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Calendar & Slots
            </button>
            <button
              onClick={() => setActiveTab("admin")}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === "admin"
                  ? "bg-white text-teal-800 shadow-xs font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Settings className="h-3.5 w-3.5" />
              <span>Admin Schedule Manager</span>
            </button>
          </div>

          <button
            onClick={() => {
              setBookingFeedback(null);
              setBookingModalOpen(true);
            }}
            className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs md:text-sm flex items-center gap-2 shadow-xs transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Schedule Patient</span>
          </button>
        </div>
      </div>

      {/* Real-world Scheduling Callout: How Overlap Prevention Works */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-teal-50/70 to-emerald-50/50 border border-teal-200/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-teal-600/10 text-teal-700 flex items-center justify-center shrink-0">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <span className="font-bold text-teal-900 text-sm">Real-World Overlap Resolution:</span>
            <p className="text-teal-800/90 mt-0.5 leading-relaxed">
              Every person is allotted <strong>30 minutes</strong> for basic consultation. Doctors cannot be double-booked at the same time. If a patient requests <strong>Saturday 11:00 AM</strong>, the AI checks all on-duty doctors. If Dr. Sarah is booked, Dr. Alex or Dr. Marcus are offered, or Dr. Sarah&apos;s next slot at 11:30 AM is suggested.
            </p>
          </div>
        </div>
        <div className="shrink-0 flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white text-teal-800 border border-teal-200 font-semibold shadow-xs">
            <CheckCircle2 className="h-3.5 w-3.5 text-teal-600" />
            Zero Time Overlaps
          </span>
        </div>
      </div>

      {activeTab === "calendar" ? (
        <div className="space-y-6">
          {/* Date & Doctor Bar */}
          <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            {/* Date Navigator */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleDateShift(-1)}
                className="p-2 rounded-xl hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors"
                title="Previous Day"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200">
                <CalendarIcon className="h-4 w-4 text-teal-600" />
                <input
                  type="date"
                  value={currentDate}
                  onChange={(e) => setCurrentDate(e.target.value)}
                  className="bg-transparent text-sm font-bold text-slate-800 focus:outline-none"
                />
              </div>
              <button
                onClick={() => handleDateShift(1)}
                className="p-2 rounded-xl hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors"
                title="Next Day"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
              <button
                onClick={() => setCurrentDate("2026-10-31")}
                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-teal-50 text-teal-700 hover:bg-teal-100 border border-teal-200 transition-colors"
              >
                Saturday Demo
              </button>
            </div>

            {/* Doctor Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
              <button
                onClick={() => setSelectedDoctorId("all")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  selectedDoctorId === "all"
                    ? "bg-slate-900 text-white shadow-xs"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                All Doctors ({doctors.length})
              </button>
              {doctors.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setSelectedDoctorId(d.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                    selectedDoctorId === d.id
                      ? "bg-teal-600 text-white shadow-xs"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: d.color }}
                  ></span>
                  <span>{d.name.split(",")[0]}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Doctor Day Columns */}
          {loading ? (
            <div className="p-16 flex flex-col items-center justify-center text-slate-400 gap-3">
              <RefreshCw className="h-6 w-6 animate-spin text-teal-600" />
              <span className="text-sm font-medium">Computing live doctor slots and checking conflicts...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {filteredDoctors.map((docCol) => (
                <div
                  key={docCol.doctor_id}
                  className="rounded-2xl bg-white border border-slate-200 shadow-xs flex flex-col overflow-hidden"
                >
                  {/* Doctor Card Header */}
                  <div className="p-4 border-b border-slate-100 bg-slate-50/50">
                    <div className="flex items-center justify-between">
                      <span
                        className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider text-white"
                        style={{ backgroundColor: docCol.color }}
                      >
                        {docCol.specialty.split("&")[0]}
                      </span>
                      <span className="text-[11px] font-medium text-slate-500">
                        {docCol.cabin}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-slate-900 mt-2 truncate">
                      {docCol.doctor_name}
                    </h3>
                    <div className="flex items-center justify-between mt-1 text-xs text-slate-500">
                      <span>
                        {docCol.is_working_today
                          ? `Hours: ${docCol.working_hours}`
                          : "Off Duty Today"}
                      </span>
                      {docCol.is_working_today && (
                        <span className="font-semibold text-teal-600">30m slots</span>
                      )}
                    </div>
                  </div>

                  {/* Slot List */}
                  <div className="p-3 space-y-2 flex-1 overflow-y-auto max-h-[500px]">
                    {!docCol.is_working_today ? (
                      <div className="p-6 text-center text-slate-400 text-xs">
                        Doctor is not scheduled to work on this day.
                      </div>
                    ) : docCol.slots.length === 0 ? (
                      <div className="p-6 text-center text-slate-400 text-xs">
                        No available slots on this date.
                      </div>
                    ) : (
                      docCol.slots.map((slot, sIdx) => {
                        const isBooked = slot.is_booked;
                        return (
                          <div
                            key={sIdx}
                            className={`p-2.5 rounded-xl border text-xs transition-all flex items-center justify-between ${
                              isBooked
                                ? "bg-slate-50 border-slate-200 text-slate-500"
                                : "bg-white hover:bg-teal-50/80 border-slate-200 hover:border-teal-300 text-slate-800 cursor-pointer shadow-2xs"
                            }`}
                            onClick={() => {
                              if (!isBooked) {
                                handleOpenBooking(docCol.doctor_id, slot.start_time);
                              }
                            }}
                          >
                            <div className="flex items-center gap-2">
                              <Clock className={`h-3.5 w-3.5 ${isBooked ? "text-slate-400" : "text-teal-600"}`} />
                              <span className="font-bold text-slate-900">
                                {slot.start_time} - {slot.end_time}
                              </span>
                            </div>

                            {isBooked ? (
                              <div className="flex items-center gap-1.5">
                                <span className="px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 text-[10px] font-semibold">
                                  Booked: {slot.booked_info?.patient_name.split(" ")[0]}
                                </span>
                                {slot.booked_info?.appointment_id && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleCancelAppointment(slot.booked_info!.appointment_id);
                                    }}
                                    className="text-rose-500 hover:text-rose-700 text-[10px] underline ml-1"
                                    title="Cancel appointment and reopen slot"
                                  >
                                    Cancel
                                  </button>
                                )}
                              </div>
                            ) : (
                              <span className="px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200 text-[10px] font-bold">
                                Available (30m)
                              </span>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Admin Doctor Roster Manager Tab */
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6">
          <div className="border-b border-slate-200 pb-4">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Settings className="h-5 w-5 text-teal-600" />
              Admin Doctor Roster & Timings Manager
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Adjust each doctor&apos;s working days, daily shift start/end times, lunch break buffers, and default consultation slot duration.
            </p>
          </div>

          {/* Select Doctor */}
          <div className="flex items-center gap-3">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Select Doctor:</label>
            <select
              value={adminSelectedDoc}
              onChange={(e) => {
                const docId = e.target.value;
                setAdminSelectedDoc(docId);
                const found = doctors.find((d) => d.id === docId);
                if (found) setAdminSchedules(found.schedules || []);
              }}
              className="px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-sm font-semibold text-slate-800 focus:outline-none focus:border-teal-500"
            >
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.specialty})
                </option>
              ))}
            </select>
          </div>

          {/* Day Schedules Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-500 font-bold uppercase tracking-wider">
                  <th className="p-3">Day</th>
                  <th className="p-3">Working Status</th>
                  <th className="p-3">Shift Start</th>
                  <th className="p-3">Shift End</th>
                  <th className="p-3">Lunch Break</th>
                  <th className="p-3">Slot Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {adminSchedules.map((dayItem, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="p-3 font-bold text-slate-800">{dayItem.day_name}</td>
                    <td className="p-3">
                      <label className="inline-flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={Boolean(dayItem.is_working)}
                          onChange={(e) => {
                            const updated = [...adminSchedules];
                            updated[idx].is_working = e.target.checked ? 1 : 0;
                            setAdminSchedules(updated);
                          }}
                          className="h-4 w-4 text-teal-600 rounded"
                        />
                        <span className={dayItem.is_working ? "font-semibold text-emerald-700" : "text-slate-400"}>
                          {dayItem.is_working ? "Active On Duty" : "Off Duty"}
                        </span>
                      </label>
                    </td>
                    <td className="p-3">
                      <input
                        type="time"
                        value={dayItem.start_time}
                        disabled={!dayItem.is_working}
                        onChange={(e) => {
                          const updated = [...adminSchedules];
                          updated[idx].start_time = e.target.value;
                          setAdminSchedules(updated);
                        }}
                        className="p-1.5 rounded-lg border border-slate-200 bg-white font-medium disabled:opacity-40"
                      />
                    </td>
                    <td className="p-3">
                      <input
                        type="time"
                        value={dayItem.end_time}
                        disabled={!dayItem.is_working}
                        onChange={(e) => {
                          const updated = [...adminSchedules];
                          updated[idx].end_time = e.target.value;
                          setAdminSchedules(updated);
                        }}
                        className="p-1.5 rounded-lg border border-slate-200 bg-white font-medium disabled:opacity-40"
                      />
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-1.5">
                        <input
                          type="time"
                          value={dayItem.lunch_start || ""}
                          placeholder="Lunch Start"
                          disabled={!dayItem.is_working}
                          onChange={(e) => {
                            const updated = [...adminSchedules];
                            updated[idx].lunch_start = e.target.value;
                            setAdminSchedules(updated);
                          }}
                          className="p-1.5 rounded-lg border border-slate-200 bg-white font-medium text-xs disabled:opacity-40"
                        />
                        <span className="text-slate-400">-</span>
                        <input
                          type="time"
                          value={dayItem.lunch_end || ""}
                          placeholder="Lunch End"
                          disabled={!dayItem.is_working}
                          onChange={(e) => {
                            const updated = [...adminSchedules];
                            updated[idx].lunch_end = e.target.value;
                            setAdminSchedules(updated);
                          }}
                          className="p-1.5 rounded-lg border border-slate-200 bg-white font-medium text-xs disabled:opacity-40"
                        />
                      </div>
                    </td>
                    <td className="p-3">
                      <select
                        value={dayItem.slot_duration_mins}
                        disabled={!dayItem.is_working}
                        onChange={(e) => {
                          const updated = [...adminSchedules];
                          updated[idx].slot_duration_mins = Number(e.target.value);
                          setAdminSchedules(updated);
                        }}
                        className="p-1.5 rounded-lg border border-slate-200 bg-white font-semibold disabled:opacity-40"
                      >
                        <option value={30}>30 Minutes (Standard)</option>
                        <option value={45}>45 Minutes (Specialized)</option>
                        <option value={60}>60 Minutes (Comprehensive)</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {rosterSuccess && (
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>{rosterSuccess}</span>
            </div>
          )}

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleSaveRoster}
              disabled={savingRoster}
              className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-xs transition-colors flex items-center gap-2"
            >
              <span>{savingRoster ? "Saving..." : "Save Doctor Roster"}</span>
            </button>
          </div>
        </div>
      )}

      {/* Booking Modal with Conflict Prevention Feedback */}
      {bookingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 border border-slate-200 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Stethoscope className="h-4 w-4 text-teal-600" />
                  Schedule Patient Consultation
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Guaranteed 30-min slot with zero double-booking overlaps.
                </p>
              </div>
              <button
                onClick={() => setBookingModalOpen(false)}
                className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-700"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Conflict Feedback Banner */}
            {bookingFeedback?.type === "conflict" && (
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-2">
                <div className="flex items-center gap-2 font-bold text-amber-800">
                  <AlertCircle className="h-4 w-4 shrink-0 text-amber-600" />
                  <span>{bookingFeedback.message}</span>
                </div>
                {bookingFeedback.alternatives?.length > 0 && (
                  <div>
                    <span className="font-semibold text-amber-950">
                      Alternative Doctors on Duty at this same time:
                    </span>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {bookingFeedback.alternatives.map((alt: any) => (
                        <button
                          key={alt.id}
                          type="button"
                          onClick={() => setModalDoctorId(alt.id)}
                          className="px-2.5 py-1 rounded-lg bg-white border border-amber-300 font-semibold text-amber-900 hover:bg-amber-100"
                        >
                          Switch to {alt.name} ({alt.specialty.split("&")[0]})
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                <p className="text-[11px] text-amber-800/80">{bookingFeedback.suggestion}</p>
              </div>
            )}

            {bookingFeedback?.type === "success" && (
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 space-y-1.5">
                <div className="flex items-center gap-2 font-bold text-emerald-800">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <span>Consultation Confirmed!</span>
                </div>
                <p>{bookingFeedback.message}</p>
                <div className="p-2.5 rounded-lg bg-white border border-emerald-200 text-[11px] text-emerald-800 space-y-1">
                  <div><strong>Email 1 (Hospital Alert):</strong> Dispatched to prahaashnms18@gmail.com</div>
                  <div><strong>Email 2 (Patient Receipt):</strong> Dispatched to {patientEmail}</div>
                </div>
              </div>
            )}

            <form onSubmit={handleBookSubmit} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Attending Doctor</label>
                  <select
                    value={modalDoctorId}
                    onChange={(e) => setModalDoctorId(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800 focus:outline-none focus:border-teal-500"
                  >
                    <option value="">Any Available Doctor</option>
                    {doctors.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.specialty})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Time Slot (30m)</label>
                  <input
                    type="time"
                    value={modalTime}
                    onChange={(e) => setModalTime(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800 focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Consultation Type</label>
                  <select
                    value={serviceType}
                    onChange={(e) => setServiceType(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800 focus:outline-none"
                  >
                    <option value="Basic Dental Consultation (30 mins)">Basic Consultation (30m)</option>
                    <option value="Orthodontic & Invisalign Assessment (45 mins)">Invisalign Assessment (45m)</option>
                    <option value="Cosmetic Veneer Consultation (45 mins)">Cosmetic Consultation (45m)</option>
                    <option value="Pediatric Cleaning & Exam (30 mins)">Pediatric Exam (30m)</option>
                    <option value="Emergency Toothache Relief (30 mins)">Emergency Relief (30m)</option>
                  </select>
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Slot Duration</label>
                  <select
                    value={modalDuration}
                    onChange={(e) => setModalDuration(Number(e.target.value))}
                    className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-medium text-slate-800"
                  >
                    <option value={30}>30 Minutes (Standard)</option>
                    <option value={45}>45 Minutes (Extended)</option>
                    <option value={60}>60 Minutes (Comprehensive)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Patient Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Johnathan Smith"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Patient Email (For Confirmation)</label>
                  <input
                    type="email"
                    required
                    placeholder="patient@email.com"
                    value={patientEmail}
                    onChange={(e) => setPatientEmail(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Patient Phone</label>
                  <input
                    type="tel"
                    placeholder="+1 (555) 019-2831"
                    value={patientPhone}
                    onChange={(e) => setPatientPhone(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Chief Complaint / Symptoms</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Sensitive lower molar, interested in 3D scan and cleaning."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setBookingModalOpen(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-100 font-semibold text-slate-600 transition-colors"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={bookingLoading}
                  className="flex-1 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold shadow-xs transition-colors"
                >
                  {bookingLoading ? "Confirming..." : "Confirm & Dispatch 2 Emails"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
