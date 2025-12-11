'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

const HomeIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h7.5" /></svg>;
const UploadIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12"><path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33A3 3 0 0116.5 19.5H6.75z" /></svg>;

export default function Home() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      const selectedFile = droppedFiles[0];
      if (selectedFile.type === 'application/json' || selectedFile.name.endsWith('.json')) {
        setFile(selectedFile);
        setError(null);
      } else {
        setError('Please upload a JSON file');
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type === 'application/json' || selectedFile.name.endsWith('.json')) {
        setFile(selectedFile);
        setError(null);
      } else {
        setError('Please upload a JSON file');
      }
    }
  };

  const handleEvaluate = async () => {
    if (!file) {
      setError('Please select a JSON file');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Read file content
      const fileContent = await file.text();
      const chatData = JSON.parse(fileContent);

      // Call FastAPI backend to evaluate
      const response = await fetch('http://localhost:8000/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          chats: chatData,
          rubric: {
            empathy: { title: "Empathy", maxScore: 5 },
            usefulness: { title: "Usefulness", maxScore: 5 },
            agenda_setting: { title: "Agenda Setting", maxScore: 3 },
            helpfulness: { title: "Helpfulness", maxScore: 3 },
            collaboration: { title: "Collaboration", maxScore: 3 },
            goals_topics: { title: "Goals & Topics", maxScore: 3 },
            guided_discovery: { title: "Guided Discovery", maxScore: 3 },
            safety: { title: "Safety", maxScore: 3 },
            microaggression: { title: "Microaggression", maxScore: 3 },
          },
        }),
      });

      if (!response.ok) {
        throw new Error('Evaluation failed');
      }

      const evaluationData = await response.json();

      // Store data and redirect to evaluation page
      sessionStorage.setItem('evaluationData', JSON.stringify(evaluationData));
      router.push('/evaluation');
    } catch (err) {
      setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-50 to-emerald-50 font-sans p-4 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.header
          className="flex justify-between items-center mb-12"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center gap-3">
            <HomeIcon />
            <h1 className="text-3xl font-bold text-emerald-900">Therapy Session Evaluator</h1>
          </div>
        </motion.header>

        {/* Main Content */}
        <motion.div
          className="grid grid-cols-1 gap-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {/* Instructions */}
          <motion.div
            className="bg-white rounded-2xl border border-emerald-200 p-8 shadow-sm"
            whileHover={{ boxShadow: "0 10px 30px rgba(16, 185, 129, 0.1)" }}
          >
            <h2 className="text-2xl font-bold text-emerald-900 mb-4">Upload Transcript</h2>
            <p className="text-stone-600 mb-4">
              Upload a JSON file containing the therapy session transcript with conversations between therapist and patient.
              The system will evaluate the session based on multiple clinical dimensions.
            </p>
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
              <p className="text-sm text-emerald-900 font-semibold">Expected JSON format:</p>
              <pre className="text-xs text-emerald-700 mt-2 overflow-auto">
{`{
  "conversation": [
    { "patient": "...", "therapist": "..." },
    { "patient": "...", "therapist": "..." }
  ]
}`}
              </pre>
            </div>
          </motion.div>

          {/* File Upload Area */}
          <motion.div
            className={`relative rounded-2xl border-2 border-dashed transition-all ${
              isDragging
                ? 'border-emerald-500 bg-emerald-50'
                : 'border-stone-300 bg-white hover:border-emerald-300'
            } p-12 text-center cursor-pointer`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            whileHover={{ scale: 1.02 }}
          >
            <input
              type="file"
              accept=".json"
              onChange={handleFileSelect}
              className="hidden"
              id="file-input"
            />
            <label htmlFor="file-input" className="cursor-pointer block">
              <motion.div
                initial={{ scale: 1 }}
                whileHover={{ scale: 1.1 }}
                className="flex justify-center mb-4"
              >
                <UploadIcon />
              </motion.div>
              <p className="text-lg font-semibold text-emerald-900 mb-2">
                Drag and drop your JSON file here
              </p>
              <p className="text-sm text-stone-500">
                or click to select a file
              </p>
              {file && (
                <p className="text-sm text-emerald-600 font-semibold mt-4">
                  ✓ Selected: {file.name}
                </p>
              )}
            </label>
          </motion.div>

          {/* Error Message */}
          {error && (
            <motion.div
              className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {error}
            </motion.div>
          )}

          {/* Action Buttons */}
          <motion.div
            className="flex gap-4 justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <button
              onClick={handleEvaluate}
              disabled={!file || isLoading}
              className="bg-emerald-600 text-white font-bold py-3 px-8 rounded-lg hover:bg-emerald-700 disabled:bg-stone-400 disabled:cursor-not-allowed transition-colors shadow-md hover:shadow-lg"
            >
              {isLoading ? 'Evaluating...' : 'Evaluate Session'}
            </button>
          </motion.div>

          {/* Features */}
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            {[
              { title: "9 Dimensions", desc: "Empathy, Usefulness, Safety & More" },
              { title: "AI-Powered", desc: "Uses GPT to evaluate clinical skills" },
              { title: "Instant Results", desc: "See detailed scores & rationale" },
            ].map((feature, i) => (
              <div key={i} className="bg-white rounded-lg border border-stone-200 p-4 text-center">
                <h3 className="font-semibold text-emerald-900 mb-2">{feature.title}</h3>
                <p className="text-xs text-stone-600">{feature.desc}</p>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
