'use client';

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

// --- ICONS ---
const HomeIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h7.5" /></svg>;
const SpinnerIcon = () => <svg aria-hidden="true" className="w-12 h-12 text-gray-200 animate-spin dark:text-gray-600 fill-emerald-600" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/><path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0492C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill"/></svg>;
const XIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>;


// --- DATA & HELPERS ---
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

// Helper to find the score in the differently-named keys
const getScore = (parsedData) => {
    if (parsedData.score !== undefined) return parsedData.score;
    const scoreKey = Object.keys(parsedData).find(key => key.includes('_score'));
    return scoreKey ? parsedData[scoreKey] : 0;
};

// --- SUB-COMPONENTS ---
const ScoreVisualizer = ({ score, maxScore }) => {
    const percentage = maxScore > 0 ? (score / maxScore) * 100 : 0;
    let colorClass = 'bg-emerald-500';
    if (percentage < 40) colorClass = 'bg-red-500';
    else if (percentage < 70) colorClass = 'bg-yellow-500';

    return (
        <div className="w-full bg-stone-200 rounded-full h-2.5 my-2">
            <div className={`${colorClass} h-2.5 rounded-full`} style={{ width: `${percentage}%` }}></div>
        </div>
    );
};

const MetricCard = ({ metricKey, data }) => {
    const definition = RUBRIC_DEFINITIONS[metricKey];
    if (!definition) return null;

    const score = getScore(data.parsed);

    return (
        <motion.div
            className="bg-white rounded-2xl border border-stone-200 p-6 flex flex-col gap-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="text-lg font-bold text-emerald-900">{definition.title}</h3>
                    <p className="text-sm text-stone-500 italic">{definition.description}</p>
                </div>
                <div className="text-2xl font-bold text-emerald-800 bg-emerald-100 rounded-lg px-3 py-1">
                    {score}<span className="text-base text-emerald-600">/{definition.maxScore}</span>
                </div>
            </div>
            <ScoreVisualizer score={score} maxScore={definition.maxScore} />
            <div>
                <h4 className="font-semibold text-stone-700 mt-2">Rationale:</h4>
                <p className="text-stone-600 text-sm leading-relaxed">{data.rationale}</p>
            </div>
        </motion.div>
    );
};

export const EvaluationLoadingScreen = () => (
    <div className="absolute inset-0 bg-stone-50/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
        <SpinnerIcon />
        <p className="mt-4 text-xl font-semibold text-emerald-800">Evaluating Session...</p>
    </div>
);


export const EndCallModal = ({ isOpen, onClose, onConfirmEnd, onConfirmEvaluate }) => {
    if (!isOpen) return null;
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
        >
            <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full"
            >
                <h2 className="text-2xl font-bold text-emerald-900 text-center">End Session</h2>
                <p className="text-center text-stone-600 mt-2 mb-8">Would you like to get a performance evaluation for this session?</p>
                <div className="flex flex-col gap-4">
                    <button onClick={onConfirmEvaluate} className="w-full bg-emerald-600 text-white font-bold py-3 px-4 rounded-xl hover:bg-emerald-700 transition-colors">
                        End Call & Evaluate
                    </button>
                    <button onClick={onConfirmEnd} className="w-full bg-stone-200 text-stone-800 font-bold py-3 px-4 rounded-xl hover:bg-stone-300 transition-colors">
                        End Call Only
                    </button>
                </div>
                <button onClick={onClose} className="absolute top-4 right-4 text-stone-400 hover:text-stone-600">
                    <XIcon />
                </button>
            </motion.div>
        </motion.div>
    );
};


// --- MAIN EVALUATION PAGE COMPONENT ---
export default function EvaluationPage({ evaluationData }) {
    const router = useRouter();
    const metricKeys = Object.keys(RUBRIC_DEFINITIONS);

    return (
        <div className="min-h-screen bg-stone-50 font-sans p-4 sm:p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <header className="flex justify-between items-center mb-8">
                    <h1 className="text-4xl font-bold text-emerald-900">Session Evaluation</h1>
                    <button
                        onClick={() => router.push('/')}
                        className="flex items-center gap-2 bg-white border border-stone-200 text-emerald-800 font-semibold py-2 px-4 rounded-lg hover:bg-stone-100 transition-colors shadow-sm"
                    >
                        <HomeIcon />
                        Return to Home
                    </button>
                </header>

                {/* Metrics Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {metricKeys.map((key) => (
                        evaluationData.details[key] && <MetricCard key={key} metricKey={key} data={evaluationData.details[key]} />
                    ))}
                </div>
            </div>
        </div>
    );
}
