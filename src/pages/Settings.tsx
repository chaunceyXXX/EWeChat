import { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Save } from 'lucide-react';
import { Config } from '../api/client';

export function Settings() {
  const { config, fetchConfig, updateConfig, isLoading } = useAppStore();
  const [formData, setFormData] = useState<Config | null>(null);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  useEffect(() => {
    if (config) setFormData(config);
  }, [config]);

  const handleChange = (section: keyof Config, key: string, value: any) => {
    if (!formData) return;
    setFormData({
      ...formData,
      [section]: typeof formData[section] === 'object'
        ? { ...formData[section] as object, [key]: value }
        : value
    });
  };
  
  // Handle root level change for monitor_folder
  const handleRootChange = (key: keyof Config, value: any) => {
      if (!formData) return;
      setFormData({
          ...formData,
          [key]: value
      });
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData) updateConfig(formData);
  };

  if (!formData) return <div className="p-8">加载中...</div>;

  return (
    <div className="p-8 max-w-4xl">
      <h2 className="text-2xl font-bold text-gray-800 mb-8">设置</h2>

      <form onSubmit={handleSubmit} className="space-y-8">
        
        {/* Monitor Folder */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-gray-800 mb-4 border-b pb-2">文件监控</h3>
          <div className="grid gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">文件夹路径</label>
              <input
                type="text"
                value={formData.monitor_folder}
                onChange={(e) => handleRootChange('monitor_folder', e.target.value)}
                placeholder="/Users/username/Documents/Reports"
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
              <p className="text-xs text-gray-500 mt-1">请输入需要监控的文件夹绝对路径。</p>
            </div>
          </div>
        </div>

        {/* WeCom Config */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-gray-800 mb-4 border-b pb-2">企业微信配置</h3>
          <div className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">企业ID (CorpID)</label>
                <input
                  type="text"
                  value={formData.wecom.corpid}
                  onChange={(e) => handleChange('wecom', 'corpid', e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">应用ID (AgentID)</label>
                <input
                  type="text"
                  value={formData.wecom.agentid}
                  onChange={(e) => handleChange('wecom', 'agentid', e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">应用密钥 (Secret)</label>
              <input
                type="password"
                value={formData.wecom.secret}
                onChange={(e) => handleChange('wecom', 'secret', e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">接收用户 (UserID)</label>
                <input
                  type="text"
                  value={formData.wecom.touser}
                  onChange={(e) => handleChange('wecom', 'touser', e.target.value)}
                  placeholder="@all"
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">接收部门 (PartyID)</label>
                <input
                  type="text"
                  value={formData.wecom.toparty}
                  onChange={(e) => handleChange('wecom', 'toparty', e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
            
            {/* Verification Config */}
            <div className="border-t pt-4 mt-2">
              <h4 className="text-sm font-bold text-gray-600 mb-3">API 接收消息配置 (用于验证)</h4>
              <div className="grid gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Token</label>
                  <input
                    type="text"
                    value={formData.wecom.token || ''}
                    onChange={(e) => handleChange('wecom', 'token', e.target.value)}
                    placeholder="在企业微信后台设置的 Token"
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">EncodingAESKey</label>
                  <input
                    type="text"
                    value={formData.wecom.aes_key || ''}
                    onChange={(e) => handleChange('wecom', 'aes_key', e.target.value)}
                    placeholder="在企业微信后台设置的 EncodingAESKey"
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* Schedule */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-gray-800 mb-4 border-b pb-2">定时任务</h3>
          <div className="flex items-center gap-4 mb-4">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.schedule.enabled}
                onChange={(e) => handleChange('schedule', 'enabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              <span className="ml-3 text-sm font-medium text-gray-900">启用定时任务</span>
            </label>
          </div>
          
          {formData.schedule.enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">频率</label>
                <select
                  value={formData.schedule.frequency}
                  onChange={(e) => handleChange('schedule', 'frequency', e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="daily">每天</option>
                  <option value="hourly">每小时</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">时间 (HH:MM)</label>
                <input
                  type="time"
                  value={formData.schedule.time}
                  onChange={(e) => handleChange('schedule', 'time', e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center gap-2 bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors font-medium shadow-lg shadow-blue-500/30"
        >
          <Save size={20} />
          {isLoading ? '保存中...' : '保存配置'}
        </button>
      </form>
    </div>
  );
}
