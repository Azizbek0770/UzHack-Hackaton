import React, { useState } from "react";
import { Send, Mail, User, MessageSquareText, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function ContactSection() {
  const [formData, setFormData] = useState({ name: "", email: "", message: "" });
  const [status, setStatus] = useState<"idle" | "sending" | "success">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("sending");

    // Simulate API call
    await new Promise((res) => setTimeout(res, 1200));

    console.log("Submitted:", formData);
    setStatus("success");

    setTimeout(() => {
      setStatus("idle");
      setFormData({ name: "", email: "", message: "" });
    }, 4000);
  };

  const inputBase =
    "w-full bg-slate-950/60 backdrop-blur border border-slate-700/40 rounded-2xl py-3 pl-12 pr-4 text-white focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 transition-all placeholder:text-slate-500";

  return (
    <section className="relative py-28 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 overflow-hidden">
      {/* Background Glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
      </div>

      <div className="max-w-5xl mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-[28px] p-8 md:p-14 shadow-[0_20px_80px_rgba(0,0,0,0.5)]"
        >
          {/* Header */}
          <div className="text-center mb-12">
            <h2 className="text-4xl font-semibold text-white tracking-tight mb-3">
              Let’s Build Something Smart
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto">
              Tell us about your workflow. We’ll design a tailored AI pipeline for your business.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Name */}
              <div className="space-y-2">
                <label className="text-sm text-slate-400 ml-1">Full Name</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    required
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="John Doe"
                    className={inputBase}
                  />
                </div>
              </div>

              {/* Email */}
              <div className="space-y-2">
                <label className="text-sm text-slate-400 ml-1">Work Email</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    required
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="you@company.com"
                    className={inputBase}
                  />
                </div>
              </div>
            </div>

            {/* Message */}
            <div className="space-y-2">
              <label className="text-sm text-slate-400 ml-1">Your Message</label>
              <div className="relative">
                <MessageSquareText className="absolute left-4 top-4 w-5 h-5 text-slate-500" />
                <textarea
                  required
                  rows={5}
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  placeholder="Describe your use case or problem..."
                  className={`${inputBase} pt-4 resize-none`}
                />
              </div>
            </div>

            {/* Button */}
            <div className="flex items-center justify-end pt-2">
              <motion.button
                whileTap={{ scale: 0.97 }}
                disabled={status === "sending"}
                className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 text-white font-medium py-3 px-8 rounded-2xl transition-all shadow-lg shadow-indigo-900/40"
              >
                {status === "success" ? (
                  <>
                    <CheckCircle2 className="w-5 h-5" />
                    Sent!
                  </>
                ) : status === "sending" ? (
                  "Sending..."
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Send Message
                  </>
                )}
              </motion.button>
            </div>
          </form>

          {/* Success Toast */}
          <AnimatePresence>
            {status === "success" && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="mt-6 text-center text-emerald-400 text-sm"
              >
                Your message has been sent successfully. We’ll be in touch soon.
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </section>
  );
}
