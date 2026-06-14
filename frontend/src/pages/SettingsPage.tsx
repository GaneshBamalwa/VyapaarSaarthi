import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Building2, Save, FileText, Phone, Mail, MapPin } from "lucide-react";
import * as api from "@/services/vyapaarApi";

export default function SettingsPage() {
  const qc = useQueryClient();
  const [formData, setFormData] = useState({
    company_name: "",
    gstin: "",
    phone: "",
    email: "",
    address: "",
  });

  const { isLoading } = useQuery({
    queryKey: ["company_profile"],
    queryFn: async () => {
      const data = await api.fetchCompanyProfile();
      setFormData({
        company_name: data.company_name || "",
        gstin: data.gstin || "",
        phone: data.phone || "",
        email: data.email || "",
        address: data.address || "",
      });
      return data;
    },
    refetchOnWindowFocus: false,
  });

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const saveMutation = useMutation({
    mutationFn: api.updateCompanyProfile,
    onSuccess: () => {
      setErrorMsg(null);
      qc.invalidateQueries({ queryKey: ["company_profile"] });
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail?.[0]?.msg || err?.response?.data?.detail || err.message || "Failed to save settings.";
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate(formData);
  };

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center border border-slate-700/50 shadow-sm">
            <Building2 size={20} className="text-slate-300" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-100">Company Settings</h1>
            <p className="text-slate-400 text-sm">Manage your business profile for automated invoicing</p>
          </div>
        </div>
      </div>

      <div className="bg-[#111113] border border-[#27272A] rounded-xl p-6 shadow-sm">
        {isLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="h-10 bg-[#18181B] rounded-lg"></div>
            <div className="h-10 bg-[#18181B] rounded-lg"></div>
            <div className="h-20 bg-[#18181B] rounded-lg"></div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="space-y-1.5">
                <label className="text-[13px] font-medium text-slate-300 flex items-center gap-1.5">
                  <Building2 size={14} className="text-slate-400" /> Company Name
                </label>
                <input
                  name="company_name"
                  value={formData.company_name}
                  onChange={handleChange}
                  required
                  placeholder="e.g. Acme Corporation"
                  className="w-full bg-[#09090B] border border-[#27272A] rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-600"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[13px] font-medium text-slate-300 flex items-center gap-1.5">
                  <FileText size={14} className="text-slate-400" /> GSTIN Number
                </label>
                <input
                  name="gstin"
                  value={formData.gstin}
                  onChange={handleChange}
                  pattern="^[0-9]{2}[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}[1-9A-Za-z]{1}Z[0-9A-Za-z]{1}$"
                  title="Must be a valid 15-character GSTIN (e.g. 29GGGGG1314R9Z6)"
                  placeholder="e.g. 29GGGGG1314R9Z6"
                  className="w-full bg-[#09090B] border border-[#27272A] rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors uppercase placeholder:text-slate-600 invalid:border-red-500/50"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[13px] font-medium text-slate-300 flex items-center gap-1.5">
                  <Phone size={14} className="text-slate-400" /> Phone Number
                </label>
                <input
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  pattern="^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$"
                  title="Must be a valid phone number with 10-15 digits"
                  placeholder="+91 98765 43210"
                  className="w-full bg-[#09090B] border border-[#27272A] rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-600 invalid:border-red-500/50"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[13px] font-medium text-slate-300 flex items-center gap-1.5">
                  <Mail size={14} className="text-slate-400" /> Email Address
                </label>
                <input
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="billing@acmecorp.com"
                  className="w-full bg-[#09090B] border border-[#27272A] rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-600"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[13px] font-medium text-slate-300 flex items-center gap-1.5">
                <MapPin size={14} className="text-slate-400" /> Billing Address
              </label>
              <textarea
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="123 Business Park, Industrial Area, Mumbai 400001"
                rows={3}
                className="w-full bg-[#09090B] border border-[#27272A] rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors resize-none placeholder:text-slate-600"
              />
            </div>

            <div className="pt-4 flex items-center justify-between border-t border-[#27272A]">
              <p className="text-xs text-slate-500">This information will be embedded in all generated PDF invoices.</p>
              <button
                type="submit"
                disabled={saveMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition disabled:opacity-50"
              >
                {saveMutation.isPending ? "Saving..." : "Save Settings"}
                <Save size={16} />
              </button>
            </div>
            {errorMsg && (
              <div className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 px-3 py-2 rounded-lg mt-3">
                Error: {errorMsg}
              </div>
            )}
            {saveMutation.isSuccess && !errorMsg && (
              <div className="text-sm text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-3 py-2 rounded-lg mt-3">
                Settings saved successfully!
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
