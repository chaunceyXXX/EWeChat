import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Play, Clock, CheckCircle, AlertCircle, UploadCloud } from 'lucide-react';

export function Dashboard() {
  const { status, config, fetchStatus, fetchConfig, runTask, uploadFile, isLoading } = useAppStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadMsg, setUploadMsg] = useState('');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      
      try {
          await uploadFile(file);
          setUploadMsg('上传成功！');
          // Clear after 3s
          setTimeout(() => setUploadMsg(''), 3000);
      } catch (err) {
          setUploadMsg('上传失败，请重试');
      }
      // Reset input
      if (fileInputRef.current) fileInputRef.current.value = '';
  };
  
  const handleDrop = async (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files?.[0];
      if (!file) return;
       try {
          await uploadFile(file);
          setUploadMsg('上传成功！');
          setTimeout(() => setUploadMsg(''), 3000);
      } catch (err) {
          setUploadMsg('上传失败，请重试');
      }
  };

  useEffect(() => {
    fetchStatus();
    fetchConfig();
    const interval = setInterval(fetchStatus, 5000); // Poll status
    return () => clearInterval(interval);
  }, [fetchStatus, fetchConfig]);

  if (!status || !config) return <div className="p-8">加载中...</div>;

  return (
    <div className="p-8 space-y-8">
      <h2 className="text-2xl font-bold text-gray-800">仪表盘</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Status Card */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-500 text-sm font-medium">系统状态</h3>
            <div className={`w-3 h-3 rounded-full ${status.running ? 'bg-green-500' : 'bg-gray-300'}`} />
          </div>
          <div className="text-2xl font-bold text-gray-800">
            {status.running ? '运行中' : '已停止'}
          </div>
        </div>

        {/* Next Run Card */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-500 text-sm font-medium">下次运行</h3>
            <Clock size={16} className="text-blue-500" />
          </div>
          <div className="text-lg font-bold text-gray-800 truncate">
            {status.next_run ? new Date(status.next_run).toLocaleString() : '未设置计划'}
          </div>
        </div>

        {/* Config Card */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-500 text-sm font-medium">监控文件夹</h3>
            <CheckCircle size={16} className="text-green-500" />
          </div>
          <div className="text-sm font-medium text-gray-800 truncate" title={config.monitor_folder}>
            {config.monitor_folder || '未配置'}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Run Task */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-bold text-gray-800 mb-4">快捷操作</h3>
            <button
            onClick={runTask}
            disabled={isLoading}
            className="flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors w-full justify-center"
            >
            <Play size={20} />
            {isLoading ? '执行中...' : '立即执行任务'}
            </button>
            <p className="mt-2 text-sm text-gray-500 text-center">
            立即手动触发扫描和发送流程。
            </p>
        </div>

        {/* Upload */}
        <div 
            className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 border-dashed border-2 hover:border-blue-400 transition-colors cursor-pointer flex flex-col items-center justify-center text-center"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
        >
            <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                onChange={handleFileChange}
            />
            <UploadCloud size={40} className="text-gray-400 mb-2" />
            <h3 className="text-lg font-bold text-gray-800">上传文件</h3>
            <p className="text-sm text-gray-500 mt-1">
                点击或拖拽文件到此处<br/>上传到监控文件夹
            </p>
            {uploadMsg && (
                <div className={`mt-2 text-sm font-bold ${uploadMsg.includes('失败') ? 'text-red-500' : 'text-green-500'}`}>
                    {uploadMsg}
                </div>
            )}
        </div>
      </div>
    </div>
  );
}
