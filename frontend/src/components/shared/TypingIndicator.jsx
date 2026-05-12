import { motion } from "framer-motion";
import { Bot } from "lucide-react";

export default function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      transition={{ duration: 0.2 }}
      className="flex gap-2.5 items-end mb-4 max-w-[min(36rem,100%)]"
    >
      <div className="w-8 h-8 rounded-xl bg-white border border-slate-100 flex items-center justify-center shrink-0 shadow-sm">
        <Bot className="w-4 h-4 text-indigo-600" />
      </div>
      <div className="bg-slate-50 border border-slate-100 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
        <div className="flex gap-1.5 items-center">
          {[0, 0.15, 0.3].map((delay, i) => (
            <motion.span
              key={i}
              className="w-1.5 h-1.5 bg-indigo-400 rounded-full block"
              animate={{ y: [0, -4, 0], opacity: [0.4, 1, 0.4] }}
              transition={{
                repeat: Infinity,
                duration: 0.9,
                delay,
                ease: "easeInOut",
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}
