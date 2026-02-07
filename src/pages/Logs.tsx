import { useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';

export function Logs() {
  const { logs, fetchLogs } = useAppStore();

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [fetchLogs]);

  return (
    <div className="p-8 h-screen flex flex-col">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold text-gray-800">系统日志</h2>
        <button 
          onClick={() => fetchLogs()}
          className="text-sm text-blue-600 hover:text-blue-800 underline"
        >
          刷新
        </button>
      </div>

      <div className="flex-1 bg-gray-900 rounded-xl p-4 overflow-auto font-mono text-sm shadow-inner">
        {logs.length === 0 ? (
          <div className="text-gray-500 text-center mt-10">暂无日志</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="mb-1">
              <span className="text-gray-500 mr-2">{index + 1}.</span>
              <span className={log.includes('ERROR') ? 'text-red-400' : 'text-green-400'}>
                {log}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
