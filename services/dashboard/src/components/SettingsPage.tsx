import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useShopContext } from "@/hooks/useShop";

export default function SettingsPage() {
  const { apiKey, logout } = useAuth();
  const { selectedShop } = useShopContext();
  const [showKey, setShowKey] = useState(false);

  const maskedKey = apiKey
    ? `${apiKey.slice(0, 4)}${"*".repeat(Math.max(0, apiKey.length - 8))}${apiKey.slice(-4)}`
    : "";

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-surface-900">Settings</h1>

      {/* API Key */}
      <div className="card">
        <h3 className="mb-4 text-lg font-semibold text-surface-900">
          API Configuration
        </h3>
        <div className="space-y-3">
          <div>
            <label className="label">API Key</label>
            <div className="flex items-center gap-2">
              <input
                type={showKey ? "text" : "password"}
                value={showKey ? apiKey ?? "" : maskedKey}
                readOnly
                className="input flex-1"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="btn-secondary"
              >
                {showKey ? "Hide" : "Show"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Active Shop */}
      <div className="card">
        <h3 className="mb-4 text-lg font-semibold text-surface-900">
          Active Shop
        </h3>
        {selectedShop ? (
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-surface-500">Name</dt>
              <dd className="font-medium text-surface-900">
                {selectedShop.name}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">Phone</dt>
              <dd className="font-medium text-surface-900">
                {selectedShop.phone_number}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">Timezone</dt>
              <dd className="font-medium text-surface-900">
                {selectedShop.timezone}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">Shop ID</dt>
              <dd className="font-mono text-xs text-surface-500">
                {selectedShop.id}
              </dd>
            </div>
          </dl>
        ) : (
          <p className="text-sm text-surface-500">
            No shop selected. Use the shop selector in the header.
          </p>
        )}
      </div>

      {/* Sign Out */}
      <div className="card">
        <h3 className="mb-4 text-lg font-semibold text-surface-900">
          Session
        </h3>
        <p className="mb-4 text-sm text-surface-500">
          Sign out to clear your API key from this browser.
        </p>
        <button onClick={logout} className="btn-primary bg-red-600 hover:bg-red-700">
          Sign Out
        </button>
      </div>
    </div>
  );
}
