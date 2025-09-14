import React, { useState } from 'react';
import { X, Settings, AlertTriangle } from 'lucide-react';
import { UserSettings } from '../types/fantasy';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: UserSettings;
  onSaveSettings: (settings: UserSettings) => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ 
  isOpen, 
  onClose, 
  settings, 
  onSaveSettings 
}) => {
  const [tempSettings, setTempSettings] = useState<UserSettings>(settings);
  const [isSaving, setIsSaving] = useState(false);

  if (!isOpen) return null;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      onSaveSettings(tempSettings);
      onClose();
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Settings size={20} className="text-fantasy-600" />
            <h2 className="text-xl font-semibold">Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sleeper League ID
            </label>
            <input
              type="text"
              value={tempSettings.leagueId}
              onChange={(e) => setTempSettings({...tempSettings, leagueId: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fantasy-500"
              placeholder="Enter your Sleeper league ID"
            />
            <p className="text-xs text-gray-500 mt-1">
              Found in your Sleeper league URL: sleeper.com/leagues/LEAGUE_ID/team
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sleeper Username
            </label>
            <input
              type="text"
              value={tempSettings.username}
              onChange={(e) => setTempSettings({...tempSettings, username: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fantasy-500"
              placeholder="Your Sleeper username"
            />
          </div>

          <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <AlertTriangle size={20} className="text-red-600" />
              <div>
                <p className="font-medium text-red-800">Brutal Mode</p>
                <p className="text-sm text-red-600">Enable brutally honest analysis</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={tempSettings.brutalMode}
                onChange={(e) => setTempSettings({...tempSettings, brutalMode: e.target.checked})}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
            </label>
          </div>

          {tempSettings.brutalMode && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                <div className="ml-3">
                  <p className="text-sm text-yellow-700">
                    <strong>Warning:</strong> Brutal mode provides unfiltered, harsh analysis of your team. 
                    The AI will not hold back on criticism but will provide actionable advice.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex space-x-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || !tempSettings.leagueId || !tempSettings.username}
            className="flex-1 px-4 py-2 bg-fantasy-600 text-white rounded-md hover:bg-fantasy-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;