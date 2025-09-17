"use client";

import { useState } from "react";
import { motion } from "motion/react";

interface Result {
  valor_risco: number;
  label: string;
  sugestao: string;
  error?: string;
}

export default function HypertensionForm() {
  const [systolic, setSystolic] = useState<number>(120);
  const [diastolic, setDiastolic] = useState<number>(80);
  const [age, setAge] = useState<number>(30);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ systolic, diastolic, age }),
      });

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({ error: "Erro ao conectar com a API" } as Result);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (label: string) => {
    switch (label) {
      case "BAIXO":
        return "bg-green-100 text-green-800";
      case "MODERADO":
        return "bg-yellow-100 text-yellow-800";
      case "ALTO":
        return "bg-orange-100 text-orange-800";
      case "CRÍTICO":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: "easeInOut" }}
      className="max-w-md mx-auto bg-white shadow-lg rounded-2xl p-6 mt-10"
    >
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeInOut" }}
        className="text-2xl font-bold text-gray-800 text-center mb-4"
      >
        Diagnóstico Fuzzy de Hipertensão
      </motion.h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <motion.div
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
        >
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pressão Sistólica (mmHg)
          </label>
          <input
            type="number"
            value={systolic}
            onChange={(e) => setSystolic(Number(e.target.value))}
            className="w-full text-black rounded-xl border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 p-2"
            min={80}
            max={200}
            required
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
        >
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pressão Diastólica (mmHg)
          </label>
          <input
            type="number"
            value={diastolic}
            onChange={(e) => setDiastolic(Number(e.target.value))}
            className="w-full text-black rounded-xl border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 p-2"
            min={50}
            max={130}
            required
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
        >
          <label className="block text-sm font-medium text-gray-700 mb-1">Idade</label>
          <input
            type="number"
            value={age}
            onChange={(e) => setAge(Number(e.target.value))}
            className="w-full text-black rounded-xl border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 p-2"
            min={0}
            max={120}
            required
          />
        </motion.div>

        <motion.button
          whileTap={{ scale: 0.9, rotate: -1.5, transition: { duration: 0.2, ease: "easeInOut" } }}
          transition={{ duration: 0.2, ease: "easeInOut" }}
          type="submit"
          className="w-full bg-blue-600 text-white rounded-xl py-2 font-semibold hover:bg-blue-700 transition disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Calculando..." : "Avaliar"}
        </motion.button>
      </form>

      {result && (
        <motion.div
          initial={{ opacity: 0, x: 100 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, ease: "easeInOut" }}
          className="mt-6 p-4 border rounded-xl bg-gray-50"
        >
          {result.error ? (
            <p className="text-red-600 text-center">{result.error}</p>
          ) : (
            <>
              <p className="text-lg font-semibold text-gray-700">Resultado:</p>
              <div
                className={`inline-block px-3 py-1 mt-2 text-sm font-medium rounded-full ${getRiskColor(
                  result.label
                )}`}
              >
                {result.label}
              </div>
              <p className="mt-2 text-gray-600">
                <strong>Score:</strong> {result.valor_risco}
              </p>
              <p className="mt-1 text-gray-600">
                <strong>Sugestão:</strong> {result.sugestao}
              </p>
            </>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
