import { useState } from 'react';
import { api } from '../api';
import ChatWidget from '../components/ChatWidget';

const PLATFORMS = ['Instagram','YouTube','TikTok','WhatsApp','LinkedIn','Twitter','Snapchat','Facebook','LINE','KakaoTalk','VKontakte','WeChat'];
const PURPOSES = ['Entertainment','Education','Networking','News'];
const STRESS = ['Low','Medium','High','Very High'];

const DEFAULTS = {
  age: 21, gender: 'Male', country: 'India', academic_level: 'Undergraduate',
  most_used_platform: 'Instagram', purpose_of_use: 'Entertainment',
  avg_daily_usage_hours: 5.5, daily_unlocks: 110, study_hours: 3.0,
  physical_activity_hours: 1.0, sleep_hours_per_night: 5.5, stress_level: 'High',
};

export default function Dashboard() {
  const [form, setForm] = useState(DEFAULTS);
  const [result, setResult] = useState(null);
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [planLoading, setPlanLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setError(''); setResult(null); setPlan(null); setLoading(true);
    try {
      const [pRes, eRes] = await Promise.all([api.predict(form), api.explain(form)]);
      if (!pRes.ok || !eRes.ok) throw new Error('Analysis failed');
      setResult({ prediction: await pRes.json(), explanation: await eRes.json() });
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handlePlan = async () => {
    setPlanLoading(true);
    try {
      const res = await api.generatePlan({ student_data: form });
      if (!res.ok) throw new Error('Plan generation failed');
      setPlan(await res.json());
    } catch (err) { setError(err.message); }
    finally { setPlanLoading(false); }
  };

  const sc = (s) => s < 4.5 ? 'text-red-500' : s < 7 ? 'text-amber-500' : 'text-emerald-500';
  const sb = (s) => s < 4.5 ? 'bg-red-50 border-red-200' : s < 7 ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50 border-emerald-200';

  return (
    <div className="max-w-6xl mx-auto p-4 pb-12">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-800">Wellness Analytics</h1>
        <p className="text-sm text-slate-500">Enter your daily habits for personalized insights powered by ML, SHAP, and RAG.</p>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* ---- FORM ---- */}
        <form onSubmit={handleAnalyze} className="lg:col-span-3 bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-5">
          <fieldset>
            <legend className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Profile</legend>
            <div className="grid grid-cols-3 gap-3">
              <Inp label="Age" type="number" value={form.age} onChange={v=>set('age',+v)} min={10} max={100} />
              <Sel label="Gender" value={form.gender} onChange={v=>set('gender',v)} opts={['Male','Female']} />
              <Inp label="Country" value={form.country} onChange={v=>set('country',v)} />
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Digital Habits</legend>
            <div className="grid grid-cols-2 gap-3">
              <Sel label="Academic Level" value={form.academic_level} onChange={v=>set('academic_level',v)} opts={['High School','Undergraduate','Graduate']} />
              <Sel label="Platform" value={form.most_used_platform} onChange={v=>set('most_used_platform',v)} opts={PLATFORMS} />
              <Sel label="Purpose" value={form.purpose_of_use} onChange={v=>set('purpose_of_use',v)} opts={PURPOSES} />
              <Inp label="Screen Time (hrs/day)" type="number" value={form.avg_daily_usage_hours} onChange={v=>set('avg_daily_usage_hours',+v)} min={0} max={24} step={0.5} />
              <Inp label="Phone Unlocks/Day" type="number" value={form.daily_unlocks} onChange={v=>set('daily_unlocks',+v)} min={0} />
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Lifestyle</legend>
            <div className="grid grid-cols-2 gap-3">
              <Inp label="Study hrs/day" type="number" value={form.study_hours} onChange={v=>set('study_hours',+v)} min={0} max={24} step={0.5} />
              <Inp label="Exercise hrs/day" type="number" value={form.physical_activity_hours} onChange={v=>set('physical_activity_hours',+v)} min={0} max={24} step={0.5} />
              <Inp label="Sleep hrs/night" type="number" value={form.sleep_hours_per_night} onChange={v=>set('sleep_hours_per_night',+v)} min={0} max={24} step={0.5} />
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Stress Level</label>
                <div className="flex gap-1">
                  {STRESS.map(s=>(
                    <button key={s} type="button" onClick={()=>set('stress_level',s)}
                      className={`flex-1 py-1.5 text-xs font-medium rounded-md transition ${form.stress_level===s?'bg-emerald-600 text-white':'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>{s}</button>
                  ))}
                </div>
              </div>
            </div>
          </fieldset>

          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={loading}
            className="w-full py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition">
            {loading ? 'Analyzing…' : 'Run Analysis'}
          </button>
        </form>

        {/* ---- RESULTS ---- */}
        <div className="lg:col-span-2 space-y-4">
          {!result && !loading && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 text-center">
              <p className="text-4xl mb-3">📊</p>
              <p className="text-sm text-slate-500">Submit the form to see your wellness score, SHAP drivers, and personalized plan.</p>
            </div>
          )}

          {loading && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 text-center">
              <div className="animate-spin h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full mx-auto mb-3"></div>
              <p className="text-sm text-slate-500">Running ML prediction & SHAP…</p>
            </div>
          )}

          {result && (<>
            {/* Score */}
            <div className={`rounded-xl border shadow-sm p-5 text-center ${sb(result.prediction.predicted_mental_health_score)}`}>
              <p className={`text-4xl font-bold font-mono ${sc(result.prediction.predicted_mental_health_score)}`}>
                {result.prediction.predicted_mental_health_score.toFixed(1)}<span className="text-lg text-slate-400">/10</span>
              </p>
              <p className="text-sm font-semibold mt-1">{result.prediction.band}</p>
              <p className="text-xs text-slate-500 mt-1">{result.prediction.summary}</p>
            </div>

            {/* SHAP */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">🔍 SHAP Drivers</h3>
              <div className="space-y-2">
                {[...result.explanation.risk_factors.slice(0,3),...result.explanation.protective_factors.slice(0,2)].map((f,i)=>(
                  <div key={i} className="flex items-center justify-between gap-2 text-xs p-2 rounded-lg bg-slate-50">
                    <div><span className="font-medium text-slate-700">{f.label}</span><span className="text-slate-400 ml-1">({f.user_value})</span></div>
                    <span className={`font-mono font-bold px-2 py-0.5 rounded ${f.impact<0?'text-red-600 bg-red-50':'text-emerald-600 bg-emerald-50'}`}>
                      {f.impact>0?'+':''}{f.impact.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Plan */}
            {!plan && (
              <button onClick={handlePlan} disabled={planLoading}
                className="w-full py-2.5 bg-emerald-700 text-white rounded-xl text-sm font-semibold hover:bg-emerald-800 disabled:opacity-50 transition">
                {planLoading ? 'Generating…' : '✨ Generate Action Plan (RAG + LLM)'}
              </button>
            )}

            {plan && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-slate-700">✨ {plan.headline}</h3>
                  <span className="text-[10px] font-mono bg-slate-100 text-slate-500 px-2 py-0.5 rounded">{plan.provider_used}</span>
                </div>
                <div className="space-y-3">
                  {plan.steps.map(s=>(
                    <div key={s.step_number} className="border-l-2 border-emerald-400 pl-3">
                      <p className="text-xs font-semibold text-slate-700">
                        <span className="inline-flex items-center justify-center w-5 h-5 bg-emerald-100 text-emerald-700 rounded text-[10px] font-bold mr-1">{s.step_number}</span>
                        {s.title}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">{s.action}</p>
                      <p className="text-[10px] text-emerald-600 mt-1 font-mono">📖 {s.source}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>)}
        </div>
      </div>

      {/* ---- EMBEDDED AI WELLNESS CHAT ---- */}
      <div className="mt-6">
        <ChatWidget studentContext={form} compact />
      </div>

      <p className="text-center text-[11px] text-slate-400 mt-8 max-w-2xl mx-auto">
        <strong>Disclaimer:</strong> MindCare Signal is an educational wellness tool, not a clinical diagnostic or treatment service.
      </p>
    </div>
  );
}

function Inp({ label, value, onChange, type='text', ...p }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-500 mb-1">{label}</label>
      <input type={type} value={value} onChange={e=>onChange(e.target.value)}
        className="w-full px-2.5 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" {...p} />
    </div>
  );
}

function Sel({ label, value, onChange, opts }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-500 mb-1">{label}</label>
      <select value={value} onChange={e=>onChange(e.target.value)}
        className="w-full px-2.5 py-1.5 border border-slate-300 rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
        {opts.map(o=><option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}
