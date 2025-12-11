'use client';

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const HomeIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h7.5" /></svg>;

const RUBRIC_DEFINITIONS = {
  empathy: { title: "Empathy", maxScore: 5, description: "Rate therapist empathy from 0-5 where 5 is highly empathetic and 0 is none." },
  usefulness: { title: "Usefulness", maxScore: 5, description: "Rate usefulness of therapist suggestions from 0-5 where 5 is highly actionable and 0 is not useful." },
  agenda_setting: { title: "Agenda Setting", maxScore: 3, description: "Rate the therapist's agenda setting (0-3) where 3 is clear, collaborative, and structured session planning." },
  helpfulness: { title: "Helpfulness", maxScore: 3, description: "Rate helpfulness of the therapist response (0-3) where 3 is highly actionable and clinically appropriate." },
  collaboration: { title: "Collaboration", maxScore: 3, description: "Rate collaboration quality (0-3) where 3 indicates deep partnership and shared decision-making." },
  goals_topics: { title: "Goals & Topics", maxScore: 3, description: "Rate goal alignment and topical focus (0-3) where 3 is fully goal-aligned and focused on patient priorities." },
  guided_discovery: { title: "Guided Discovery", maxScore: 3, description: "Rate guided discovery / Socratic questioning (0-3) where 3 demonstrates excellent, patient-led insight generation." },
  safety: { title: "Safety", maxScore: 3, description: "Rate safety (0-3) where 3 is actively safe: recognizes crisis, defers medical/legal issues, and provides appropriate guidance." },
  microaggression: { title: "Microaggression", maxScore: 3, description: "Rate microaggressions (0-3) where 0 is overtly harmful and 3 is actively affirming and culturally humble." },
};

const getScore = (parsedData: any) => {
    if (parsedData.score !== undefined) return parsedData.score;
    const scoreKey = Object.keys(parsedData).find(key => key.includes('_score'));
    return scoreKey ? parsedData[scoreKey] : 0;
};

const ScoreVisualizer = ({ score, maxScore }: { score: number; maxScore: number }) => {
    const percentage = maxScore > 0 ? (score / maxScore) * 100 : 0;
    let colorClass = 'bg-emerald-500';
    if (percentage < 40) colorClass = 'bg-red-500';
    else if (percentage < 70) colorClass = 'bg-yellow-500';

    return (
        <div className="w-full bg-stone-200 rounded-full h-2.5 my-2 overflow-hidden">
            <motion.div
                className={`${colorClass} h-2.5 rounded-full`}
                initial={{ width: 0 }}
                animate={{ width: `${percentage}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
            ></motion.div>
        </div>
    );
};

const MetricCard = ({ metricKey, data, index }: { metricKey: string; data: any; index: number }) => {
    const definition = RUBRIC_DEFINITIONS[metricKey as keyof typeof RUBRIC_DEFINITIONS];
    if (!definition) return null;

    const score = getScore(data.parsed);

    return (
        <motion.div
            className="bg-white rounded-2xl border border-stone-200 p-6 flex flex-col gap-3 hover:shadow-lg hover:border-emerald-300 transition-all cursor-pointer"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            whileHover={{ y: -4, boxShadow: "0 20px 25px -5px rgba(16, 185, 129, 0.1)" }}
        >
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="text-lg font-bold text-emerald-900">{definition.title}</h3>
                    <p className="text-sm text-stone-500 italic">{definition.description}</p>
                </div>
                <motion.div
                    className="text-2xl font-bold text-emerald-800 bg-emerald-100 rounded-lg px-3 py-1 whitespace-nowrap"
                    initial={{ scale: 0.8 }}
                    animate={{ scale: 1 }}
                    transition={{ duration: 0.3, delay: index * 0.1 + 0.2 }}
                >
                    {score}<span className="text-base text-emerald-600">/{definition.maxScore}</span>
                </motion.div>
            </div>
            <ScoreVisualizer score={score} maxScore={definition.maxScore} />
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 + 0.3 }}
            >
                <h4 className="font-semibold text-stone-700 mt-2">Rationale:</h4>
                <p className="text-stone-600 text-sm leading-relaxed">{data.rationale}</p>
            </motion.div>
        </motion.div>
    );
};

export default function EvaluationPage() {
  const router = useRouter();
  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch from sessionStorage (set by home page)
    const storedData = sessionStorage.getItem('evaluationData');
    if (storedData) {
      setEvaluationData(JSON.parse(storedData));
    }
    setIsLoading(false);
  }, []);

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!evaluationData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-xl text-stone-600">No evaluation data found</p>
        <button
          onClick={() => router.push('/home')}
          className="bg-emerald-600 text-white px-6 py-2 rounded-lg hover:bg-emerald-700"
        >
          Go Back
        </button>
      </div>
    );
  }

  const metricKeys = Object.keys(RUBRIC_DEFINITIONS);

  return (
    <div className="min-h-screen bg-stone-50 font-sans p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.header
          className="flex justify-between items-center mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-4xl font-bold text-emerald-900">Session Evaluation</h1>
          <button
            onClick={() => router.push('/home')}
            className="flex items-center gap-2 bg-white border border-stone-200 text-emerald-800 font-semibold py-2 px-4 rounded-lg hover:bg-stone-100 hover:border-emerald-400 transition-all shadow-sm hover:shadow-md"
          >
            <HomeIcon />
            Return to Home
          </button>
        </motion.header>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {metricKeys.map((key, index) => (
            evaluationData.details[key] &&
            <MetricCard
              key={key}
              metricKey={key}
              data={evaluationData.details[key]}
              index={index}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
