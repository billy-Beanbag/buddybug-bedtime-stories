"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ApiKeyTable } from "@/components/admin/ApiKeyTable";
import { CreateApiKeyForm, type CreateApiKeyFormValue } from "@/components/admin/CreateApiKeyForm";
import { useAuth } from "@/context/AuthContext";
import { apiDelete, apiGet, apiPost } from "@/lib/api";
import type { ApiKeyCreateResponse, ApiKeyRead } from "@/lib/types";

export default function AdminApiKeysPage() {
  const { token, isAdmin } = useAuth();
  const [apiKeys, setApiKeys] = useState<ApiKeyRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deactivatingId, setDeactivatingId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [newRawKey, setNewRawKey] = useState<string | null>(null);

  async function loadApiKeys() {
    if (!token) {
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await apiGet<ApiKeyRead[]>("/admin/api-keys", { token });
      setApiKeys(response);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to load API keys");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadApiKeys();
    }
  }, [token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage API keys." />;
  }

  if (loading) {
    return <LoadingState message="Loading API keys..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">API keys and integrations</h1>
        <p className="mt-2 text-sm text-slate-600">
          Issue scoped server-to-server keys for narrow Buddybug reporting and discovery integrations. Raw keys are shown only once.
        </p>
      </section>

      <CreateApiKeyForm
        submitting={creating}
        onSubmit={async (value: CreateApiKeyFormValue) => {
          if (!token) {
            return;
          }
          setCreating(true);
          setStatusMessage(null);
          setErrorMessage(null);
          setNewRawKey(null);
          try {
            const response = await apiPost<ApiKeyCreateResponse>("/admin/api-keys", value, { token });
            setNewRawKey(response.raw_api_key);
            setStatusMessage(`Created API key "${response.key.name}". Copy it now; Buddybug will not show it again.`);
            await loadApiKeys();
          } catch (err) {
            setErrorMessage(err instanceof Error ? err.message : "Unable to create API key");
          } finally {
            setCreating(false);
          }
        }}
      />

      {newRawKey ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-amber-900">Copy this API key now</h2>
          <p className="mt-2 text-sm text-amber-800">
            This secret is only returned once at creation time. Store it in your integration environment securely.
          </p>
          <code className="mt-4 block overflow-x-auto rounded-2xl bg-white px-4 py-3 text-sm text-slate-900">{newRawKey}</code>
        </section>
      ) : null}

      {statusMessage ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div>
      ) : null}

      <ApiKeyTable
        apiKeys={apiKeys}
        deactivatingId={deactivatingId}
        onDeactivate={async (apiKey) => {
          if (!token) {
            return;
          }
          setDeactivatingId(apiKey.id);
          setStatusMessage(null);
          setErrorMessage(null);
          try {
            await apiDelete(`/admin/api-keys/${apiKey.id}`, { token });
            setStatusMessage(`Deactivated API key "${apiKey.name}".`);
            await loadApiKeys();
          } catch (err) {
            setErrorMessage(err instanceof Error ? err.message : "Unable to deactivate API key");
          } finally {
            setDeactivatingId(null);
          }
        }}
      />
    </div>
  );
}
